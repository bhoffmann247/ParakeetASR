# Migration Guide: Pyannote to NeMo Diarization

This guide explains the changes made when switching from Pyannote.audio to NVIDIA NeMo for speaker diarization.

## What Changed

### Dependencies
- **Removed**: `pyannote-audio` dependency
- **Added**: `omegaconf` dependency (required for NeMo configuration)
- **Kept**: `nemo_toolkit` (was already included)

### Authentication
- **Before**: Required HuggingFace account and access token
- **After**: No external authentication required - NeMo models are publicly available

### Configuration
- **Removed**: All HuggingFace token handling
- **Removed**: `HUGGINGFACE_ACCESS_TOKEN` environment variable requirement
- **Removed**: `--hf-token` command line argument from `run.sh`

### API Changes
- **No breaking changes**: All API endpoints remain the same
- **Behavior**: Diarization now uses NeMo's ClusteringDiarizer instead of Pyannote
- **Performance**: May see different speaker detection accuracy/behavior

## Migration Steps

### 1. Update Dependencies
```bash
pip install -r requirements.txt
```

### 2. Remove HuggingFace Token (Optional)
You can remove any HuggingFace token environment variables as they're no longer needed:
```bash
unset HUGGINGFACE_ACCESS_TOKEN
```

### 3. Test the New Implementation
Run the test script to verify NeMo diarization works:
```bash
python test_nemo_diarization.py
```

### 4. Update Your Scripts
If you have any scripts that set HuggingFace tokens, you can remove those lines:

**Before:**
```bash
./run.sh --hf-token "your_token_here"
```

**After:**
```bash
./run.sh
```

## Benefits of the Migration

### Simplified Setup
- No need to create HuggingFace accounts
- No need to accept model agreements
- No token management required

### Better Integration
- NeMo is already used for the ASR model (Parakeet-TDT)
- Consistent NVIDIA ecosystem
- Potentially better performance integration

### Reduced Dependencies
- One less external service dependency
- Simplified deployment and configuration

## Potential Differences

### Speaker Detection
- NeMo may detect speakers differently than Pyannote
- Speaker labels may be formatted slightly differently
- Number of detected speakers might vary for the same audio

### Performance
- Different computational characteristics
- May be faster or slower depending on your hardware
- Different memory usage patterns

## Troubleshooting

### Import Errors
If you see import errors related to NeMo:
```bash
pip install --upgrade nemo_toolkit
```

### Configuration Issues
If diarization fails to initialize:
1. Check that `nemo_toolkit` is properly installed
2. Verify CUDA is available if using GPU
3. Check the logs for specific error messages

### Model Download Issues
NeMo will automatically download required models on first use. Ensure you have:
- Internet connection
- Sufficient disk space
- Write permissions in the temp directory

## Rollback (If Needed)

If you need to rollback to Pyannote:

1. **Restore requirements.txt:**
   ```
   # Add back: pyannote-audio
   # Remove: omegaconf
   ```

2. **Restore the old diarization code** from your git history

3. **Restore HuggingFace token handling** in config.py, api.py, and run.sh

## Support

If you encounter issues with the migration:
1. Check the logs for specific error messages
2. Run the test script: `python test_nemo_diarization.py`
3. Verify your NeMo installation: `python -c "import nemo; print(nemo.__version__)"`