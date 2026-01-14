# Speaker diarization module for Parakeet
# This module integrates NVIDIA NeMo for speaker identification

from typing import Dict, List, Optional, Tuple, Union
import os
import logging
import tempfile
import json
import numpy as np
import torch
from pydantic import BaseModel
from omegaconf import OmegaConf

logger = logging.getLogger(__name__)

class SpeakerSegment(BaseModel):
    """A segment of speech from a specific speaker"""
    start: float
    end: float
    speaker: str

class DiarizationResult(BaseModel):
    """Result of speaker diarization"""
    segments: List[SpeakerSegment]
    num_speakers: int

class Diarizer:
    """Speaker diarization using NVIDIA NeMo"""

    def __init__(self):
        self.diarizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.temp_dir = tempfile.mkdtemp()
        self.enabled = False
        self._initialize()

    def _initialize(self):
        """Initialize the NeMo diarization pipeline"""
        try:
            from nemo.collections.asr.models import ClusteringDiarizer
            
            logger.info("Initializing NeMo ClusteringDiarizer...")
            
            # Create configuration based on the working GitHub gist example
            config = OmegaConf.create({
                'device': self.device,  # KEY: This was missing!
                'num_workers': 0,  # Set to 0 to avoid multiprocessing issues on Windows
                'sample_rate': 16000,  # Required for VAD processing
                'verbose': True,  # Enable verbose output
                'diarizer': {
                    'manifest_filepath': None,
                    'out_dir': self.temp_dir,
                    'oracle_vad': False,
                    'collar': 0.25,
                    'ignore_overlap': True,
                    'vad': {
                        'model_path': 'vad_multilingual_marblenet',
                        'parameters': {
                            'window_length_in_sec': 0.15,
                            'shift_length_in_sec': 0.01,
                            'smoothing': False,
                            'overlap': 0.5,
                            'onset': 0.8,
                            'offset': 0.6,
                            'pad_onset': 0.05,
                            'pad_offset': -0.05,
                            'min_duration_on': 0.2,
                            'min_duration_off': 0.2,
                            'filter_speech_first': True
                        }
                    },
                    'speaker_embeddings': {
                        'model_path': 'titanet_large',
                        'parameters': {
                            'window_length_in_sec': 1.5,
                            'shift_length_in_sec': 0.75,
                            'multiscale_weights': None,
                            'save_embeddings': False
                        },
                        'batch_size': 1  # Use batch_size=1 to avoid tensor dimension issues on Windows
                    },
                    'clustering': {
                        'parameters': {
                            'oracle_num_speakers': False,
                            'max_num_speakers': 8,
                            'enhanced_count_thres': 40,
                            'max_rp_threshold': 0.25,
                            'sparse_search_volume': 30
                        }
                    }
                }
            })
            
            # Initialize the diarizer
            logger.info("Creating ClusteringDiarizer instance...")
            self.diarizer = ClusteringDiarizer(cfg=config).to(self.device)
            self.enabled = True
            logger.info(f"✅ NeMo diarization pipeline initialized successfully on {self.device}")

        except Exception as e:
            logger.error(f"❌ Failed to initialize NeMo diarization pipeline: {str(e)}")
            logger.warning("Diarization will be disabled. Transcription will continue without speaker labels.")
            import traceback
            traceback.print_exc()
            self.diarizer = None
            self.enabled = False

    def diarize(self, audio_path: str, num_speakers: Optional[int] = None) -> DiarizationResult:
        """
        Perform speaker diarization on an audio file using NeMo

        Args:
            audio_path: Path to the audio file
            num_speakers: Optional number of speakers (if known)

        Returns:
            DiarizationResult with speaker segments
        """
        if not self.enabled or self.diarizer is None:
            logger.warning("NeMo diarization is disabled, returning empty result")
            return DiarizationResult(segments=[], num_speakers=0)

        try:
            # Try using the standard ClusteringDiarizer approach first
            return self._diarize_with_clustering(audio_path, num_speakers)
        except Exception as e:
            logger.warning(f"ClusteringDiarizer failed: {str(e)}")
            logger.info("Attempting manual diarization approach for Windows CPU compatibility...")
            try:
                return self._diarize_manual(audio_path, num_speakers)
            except Exception as e2:
                logger.error(f"❌ Manual diarization also failed: {str(e2)}")
                import traceback
                traceback.print_exc()
                return DiarizationResult(segments=[], num_speakers=0)

    def _diarize_with_clustering(self, audio_path: str, num_speakers: Optional[int] = None) -> DiarizationResult:
        """Standard ClusteringDiarizer approach"""
        # Create manifest file for NeMo
        manifest_path = os.path.join(self.temp_dir, "input_manifest.json")
        
        # Get audio file info
        import librosa
        duration = librosa.get_duration(path=audio_path)
        
        # Get base filename for RTTM output
        audio_file_name = os.path.splitext(os.path.basename(audio_path))[0]
        
        # Create manifest entry
        manifest_entry = {
            "audio_filepath": audio_path,
            "offset": 0,
            "duration": duration,
            "label": "infer",
            "text": "-",
            "num_speakers": num_speakers if num_speakers else None,
            "rttm_filepath": None,
            "uem_filepath": None
        }
        
        # Write manifest file
        with open(manifest_path, 'w') as f:
            json.dump(manifest_entry, f)
            f.write('\n')
        
        # Update diarizer config with manifest path
        self.diarizer._cfg.diarizer.manifest_filepath = manifest_path
        
        # Set number of speakers if provided
        if num_speakers is not None:
            self.diarizer._cfg.diarizer.clustering.parameters.oracle_num_speakers = True
            self.diarizer._cfg.diarizer.clustering.parameters.max_num_speakers = num_speakers
        
        # Run diarization
        logger.info(f"Running NeMo diarization on {audio_path}")
        self.diarizer.diarize()
        logger.info("NeMo diarization completed")
        
        # Parse results from RTTM file
        rttm_dir = os.path.join(self.temp_dir, "pred_rttms")
        rttm_path = os.path.join(rttm_dir, f"{audio_file_name}.rttm")
        
        return self._parse_rttm(rttm_path)

    def _diarize_manual(self, audio_path: str, num_speakers: Optional[int] = None) -> DiarizationResult:
        """
        Manual diarization approach that bypasses the ClusteringDiarizer dataloader.
        This works on Windows CPU by directly using the VAD and speaker models.
        """
        from nemo.collections.asr.models import EncDecSpeakerLabelModel, EncDecClassificationModel
        from sklearn.cluster import AgglomerativeClustering
        from pydub import AudioSegment
        import librosa
        
        logger.info("Using manual diarization approach (Windows CPU compatible)")
        
        # Step 1: Voice Activity Detection
        logger.info("Step 1: Running VAD...")
        vad_segments = self._run_vad_manual(audio_path)
        logger.info(f"Found {len(vad_segments)} speech segments")
        
        if not vad_segments:
            logger.warning("No speech detected")
            return DiarizationResult(segments=[], num_speakers=0)
        
        # Step 2: Extract speaker embeddings for each segment
        logger.info("Step 2: Extracting speaker embeddings...")
        embeddings, valid_segments = self._extract_embeddings_manual(audio_path, vad_segments)
        logger.info(f"Extracted {len(embeddings)} embeddings")
        
        if len(embeddings) == 0:
            logger.warning("No embeddings extracted")
            return DiarizationResult(segments=[], num_speakers=0)
        
        # Step 3: Cluster embeddings to identify speakers
        logger.info("Step 3: Clustering speakers...")
        speaker_labels = self._cluster_embeddings(embeddings, num_speakers)
        
        # Step 4: Create speaker segments
        segments = []
        speakers = set()
        
        for (start, end), label in zip(valid_segments, speaker_labels):
            speaker_id = f"speaker_SPEAKER_{label:02d}"
            segments.append(SpeakerSegment(
                start=start,
                end=end,
                speaker=speaker_id
            ))
            speakers.add(speaker_id)
        
        # Sort segments by start time
        segments.sort(key=lambda x: x.start)
        
        logger.info(f"✅ Manual diarization found {len(speakers)} speakers with {len(segments)} segments")
        
        return DiarizationResult(
            segments=segments,
            num_speakers=len(speakers)
        )

    def _run_vad_manual(self, audio_path: str) -> List[Tuple[float, float]]:
        """Run VAD manually to get speech segments"""
        try:
            from nemo.collections.asr.parts.utils.vad_utils import generate_vad_segment_table
            import soundfile as sf
            
            # Load audio
            audio, sr = sf.read(audio_path)
            
            # Get VAD model from diarizer
            vad_model = self.diarizer._vad_model
            
            # Process audio in chunks
            frame_len = 0.15  # 150ms
            hop_len = 0.01    # 10ms
            
            # Get VAD predictions
            vad_probs = []
            chunk_size = int(sr * frame_len)
            hop_size = int(sr * hop_len)
            
            for i in range(0, len(audio) - chunk_size, hop_size):
                chunk = audio[i:i + chunk_size]
                # Pad if needed
                if len(chunk) < chunk_size:
                    chunk = np.pad(chunk, (0, chunk_size - len(chunk)))
                
                # Get VAD probability (simplified - just use threshold on energy)
                energy = np.sqrt(np.mean(chunk ** 2))
                vad_probs.append(energy)
            
            # Convert probabilities to segments
            threshold = np.median(vad_probs) * 0.5
            is_speech = np.array(vad_probs) > threshold
            
            # Find continuous speech segments
            segments = []
            in_speech = False
            start_idx = 0
            
            for i, speech in enumerate(is_speech):
                if speech and not in_speech:
                    start_idx = i
                    in_speech = True
                elif not speech and in_speech:
                    start_time = start_idx * hop_len
                    end_time = i * hop_len
                    if end_time - start_time > 0.5:  # Minimum 0.5s segments
                        segments.append((start_time, end_time))
                    in_speech = False
            
            # Handle last segment
            if in_speech:
                start_time = start_idx * hop_len
                end_time = len(is_speech) * hop_len
                if end_time - start_time > 0.5:
                    segments.append((start_time, end_time))
            
            return segments
            
        except Exception as e:
            logger.error(f"VAD failed: {e}")
            # Fallback: treat entire audio as one segment
            import librosa
            duration = librosa.get_duration(path=audio_path)
            return [(0.0, duration)]

    def _extract_embeddings_manual(self, audio_path: str, segments: List[Tuple[float, float]]) -> Tuple[List[np.ndarray], List[Tuple[float, float]]]:
        """Extract speaker embeddings manually using TitaNet"""
        from nemo.collections.asr.models import EncDecSpeakerLabelModel
        from pydub import AudioSegment
        import tempfile
        
        # Get speaker model from diarizer
        speaker_model = self.diarizer._speaker_model
        
        # Load full audio
        audio = AudioSegment.from_wav(audio_path)
        
        embeddings = []
        valid_segments = []
        
        for start, end in segments:
            try:
                # Extract segment
                start_ms = int(start * 1000)
                end_ms = int(end * 1000)
                segment_audio = audio[start_ms:end_ms]
                
                # Skip very short segments
                if len(segment_audio) < 500:  # Less than 0.5 seconds
                    continue
                
                # Save to temporary file
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                    tmp_path = tmp_file.name
                    segment_audio.export(tmp_path, format='wav')
                
                # Extract embedding using TitaNet's get_embedding method
                embedding = speaker_model.get_embedding(tmp_path)
                
                # Clean up
                os.remove(tmp_path)
                
                # Convert to numpy if needed
                if torch.is_tensor(embedding):
                    embedding = embedding.cpu().numpy().squeeze()
                
                embeddings.append(embedding)
                valid_segments.append((start, end))
                
            except Exception as e:
                logger.warning(f"Failed to extract embedding for segment {start}-{end}: {e}")
                continue
        
        return embeddings, valid_segments

    def _cluster_embeddings(self, embeddings: List[np.ndarray], num_speakers: Optional[int] = None) -> List[int]:
        """Cluster embeddings to identify speakers"""
        from sklearn.cluster import AgglomerativeClustering
        from sklearn.metrics import silhouette_score
        
        embeddings_array = np.array(embeddings)
        
        # Determine number of speakers if not provided
        if num_speakers is None:
            # Try different numbers of clusters and pick the best
            best_score = -1
            best_n = 2
            
            for n in range(2, min(9, len(embeddings))):
                clustering = AgglomerativeClustering(n_clusters=n, metric='cosine', linkage='average')
                labels = clustering.fit_predict(embeddings_array)
                
                if len(set(labels)) > 1:
                    score = silhouette_score(embeddings_array, labels, metric='cosine')
                    if score > best_score:
                        best_score = score
                        best_n = n
            
            num_speakers = best_n
            logger.info(f"Auto-detected {num_speakers} speakers")
        
        # Final clustering
        clustering = AgglomerativeClustering(
            n_clusters=num_speakers,
            metric='cosine',
            linkage='average'
        )
        labels = clustering.fit_predict(embeddings_array)
        
        return labels.tolist()

    def _parse_rttm(self, rttm_path: str) -> DiarizationResult:
        """Parse RTTM file to extract speaker segments"""
        segments = []
        speakers = set()
        
        if os.path.exists(rttm_path):
            logger.info(f"Reading RTTM file: {rttm_path}")
            with open(rttm_path, 'r') as f:
                for line in f:
                    if line.strip():
                        parts = line.strip().split()
                        if len(parts) >= 8 and parts[0] == "SPEAKER":
                            start_time = float(parts[3])
                            duration_val = float(parts[4])
                            end_time = start_time + duration_val
                            speaker_id = parts[7]
                            
                            # Format speaker ID consistently
                            formatted_speaker = f"speaker_SPEAKER_{speaker_id}"
                            
                            segments.append(SpeakerSegment(
                                start=start_time,
                                end=end_time,
                                speaker=formatted_speaker
                            ))
                            speakers.add(speaker_id)
        else:
            logger.warning(f"RTTM file not found: {rttm_path}")
        
        # Sort segments by start time
        segments.sort(key=lambda x: x.start)
        
        logger.info(f"✅ Parsed {len(speakers)} speakers with {len(segments)} segments from RTTM")
        
        return DiarizationResult(
            segments=segments,
            num_speakers=len(speakers)
        )

    def merge_with_transcription(self,
                                diarization: DiarizationResult,
                                transcription_segments: list) -> list:
        """
        Merge diarization results with transcription segments

        Args:
            diarization: Speaker diarization result
            transcription_segments: List of transcription segments with start/end times

        Returns:
            Merged list of segments with speaker information
        """
        # If no diarization results, return original transcription
        if not diarization.segments:
            return transcription_segments

        # For each transcription segment, find the dominant speaker
        for segment in transcription_segments:
            # Get segment time bounds
            start = segment.start
            end = segment.end

            # Find overlapping diarization segments
            overlapping = []
            for spk_segment in diarization.segments:
                # Calculate overlap
                overlap_start = max(start, spk_segment.start)
                overlap_end = min(end, spk_segment.end)

                if overlap_end > overlap_start:
                    # There is an overlap
                    duration = overlap_end - overlap_start
                    overlapping.append((spk_segment.speaker, duration))

            # Assign the speaker with most overlap
            if overlapping:
                # Sort by duration (descending) and pick the longest
                overlapping.sort(key=lambda x: x[1], reverse=True)
                dominant_speaker = overlapping[0][0]
                segment.speaker = dominant_speaker

        return transcription_segments
