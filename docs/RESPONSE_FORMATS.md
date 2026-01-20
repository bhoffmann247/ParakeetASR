# Supported Response Formats

The Parakeet API supports 5 different response formats, compatible with the OpenAI Whisper API.

## Format Overview

| Format | Description | Use Case |
|--------|-------------|----------|
| `json` | Structured JSON with text and metadata | Default, API integration |
| `text` | Plain text transcription only | Simple text extraction |
| `srt` | SubRip subtitle format | Video subtitles |
| `vtt` | WebVTT subtitle format | Web video subtitles |
| `verbose_json` | JSON with detailed segments | Advanced processing |

---

## 1. JSON Format (Default)

**Parameter**: `response_format=json`

**Description**: Returns a structured JSON response with the transcription text and metadata.

**Example Request**:
```powershell
curl.exe -X POST http://localhost:8000/v1/audio/transcriptions `
  -F "file=@audio.wav" `
  -F "model=parakeet-tdt-0.6b-v2" `
  -F "response_format=json"
```

**Example Response**:
```json
{
  "text": "Hi, my name is Xavier. Thank you for calling Customer Care.",
  "language": null,
  "task": "transcribe",
  "duration": 5.39,
  "model": "parakeet-tdt-0.6b-v2"
}
```

**With Diarization**:
```json
{
  "text": "Speaker 1: Hi, my name is Xavier. Speaker 2: Thank you for calling.",
  "language": null,
  "task": "transcribe",
  "duration": 5.39,
  "model": "parakeet-tdt-0.6b-v2"
}
```

**Use Cases**:
- API integration
- Programmatic processing
- Storing transcriptions in databases
- Further text analysis

---

## 2. Text Format

**Parameter**: `response_format=text`

**Description**: Returns only the transcription text as plain text, without any metadata or formatting.

**Example Request**:
```powershell
curl.exe -X POST http://localhost:8000/v1/audio/transcriptions `
  -F "file=@audio.wav" `
  -F "model=parakeet-tdt-0.6b-v2" `
  -F "response_format=text"
```

**Example Response**:
```
Hi, my name is Xavier. Thank you for calling Customer Care. May I please get your name, phone, and email?
```

**With Diarization**:
```
Speaker 1: Hi, my name is Xavier. Speaker 2: Thank you for calling Customer Care.
```

**Use Cases**:
- Simple text extraction
- Copy-paste workflows
- Text-only applications
- Minimal overhead

---

## 3. SRT Format (SubRip)

**Parameter**: `response_format=srt`

**Description**: Returns subtitles in SubRip (.srt) format with timestamps and segment numbers.

**Example Request**:
```powershell
curl.exe -X POST http://localhost:8000/v1/audio/transcriptions `
  -F "file=@audio.wav" `
  -F "model=parakeet-tdt-0.6b-v2" `
  -F "response_format=srt"
```

**Example Response**:
```srt
1
0:00:05,760 --> 0:00:07,040
Hi, my name is Xavier.

2
0:00:07,120 --> 0:00:08,880
Thank you for calling Customer Care.

3
0:00:08,960 --> 0:00:11,440
May I please get your name, phone, and email?
```

**Format Details**:
- Segment number
- Start time --> End time (HH:MM:SS,mmm)
- Text content
- Blank line separator

**Use Cases**:
- Video subtitles
- Movie/TV show captions
- YouTube subtitles
- Media players (VLC, etc.)

---

## 4. VTT Format (WebVTT)

**Parameter**: `response_format=vtt`

**Description**: Returns subtitles in WebVTT format, designed for web video players.

**Example Request**:
```powershell
curl.exe -X POST http://localhost:8000/v1/audio/transcriptions `
  -F "file=@audio.wav" `
  -F "model=parakeet-tdt-0.6b-v2" `
  -F "response_format=vtt"
```

**Example Response**:
```vtt
WEBVTT

0:00:05.760 --> 0:00:07.040
Hi, my name is Xavier.

0:00:07.120 --> 0:00:08.880
Thank you for calling Customer Care.

0:00:08.960 --> 0:00:11.440
May I please get your name, phone, and email?
```

**Format Details**:
- Starts with "WEBVTT" header
- Start time --> End time (HH:MM:SS.mmm)
- Text content
- Blank line separator

**Use Cases**:
- HTML5 video players
- Web-based video platforms
- Streaming services
- Accessible web content

---

## 5. Verbose JSON Format

**Parameter**: `response_format=verbose_json`

**Description**: Returns detailed JSON with individual segments, timestamps, and metadata.

**Example Request**:
```powershell
curl.exe -X POST http://localhost:8000/v1/audio/transcriptions `
  -F "file=@audio.wav" `
  -F "model=parakeet-tdt-0.6b-v2" `
  -F "response_format=verbose_json"
```

**Example Response**:
```json
{
  "text": "Hi, my name is Xavier. Thank you for calling Customer Care.",
  "segments": [
    {
      "id": 0,
      "start": 5.76,
      "end": 7.04,
      "text": "Hi, my name is Xavier.",
      "speaker": null
    },
    {
      "id": 1,
      "start": 7.12,
      "end": 8.88,
      "text": "Thank you for calling Customer Care.",
      "speaker": null
    }
  ],
  "language": null,
  "task": "transcribe",
  "duration": 5.39,
  "model": "parakeet-tdt-0.6b-v2"
}
```

**With Diarization**:
```json
{
  "text": "Speaker 1: Hi, my name is Xavier. Speaker 2: Thank you.",
  "segments": [
    {
      "id": 0,
      "start": 5.76,
      "end": 7.04,
      "text": "Hi, my name is Xavier.",
      "speaker": "Speaker 1"
    },
    {
      "id": 1,
      "start": 7.12,
      "end": 8.88,
      "text": "Thank you.",
      "speaker": "Speaker 2"
    }
  ],
  "language": null,
  "task": "transcribe",
  "duration": 5.39,
  "model": "parakeet-tdt-0.6b-v2"
}
```

**Use Cases**:
- Detailed analysis
- Timeline visualization
- Speaker tracking
- Advanced processing
- Editing applications

---

## Comparison Table

| Feature | json | text | srt | vtt | verbose_json |
|---------|------|------|-----|-----|--------------|
| Full text | ✓ | ✓ | ✓ | ✓ | ✓ |
| Timestamps | - | - | ✓ | ✓ | ✓ |
| Segments | - | - | ✓ | ✓ | ✓ |
| Metadata | ✓ | - | - | - | ✓ |
| Speaker labels | ✓ | ✓ | ✓ | ✓ | ✓ |
| Segment details | - | - | - | - | ✓ |
| File size | Small | Smallest | Medium | Medium | Largest |
| Parsing | Easy | Easiest | Medium | Medium | Easy |

---

## Testing All Formats

You can test all formats using the test script:

```powershell
.\test-api.ps1 -SkipBuild -SkipStartup
```

Or manually test each format:

### JSON
```powershell
curl.exe -X POST http://localhost:8000/v1/audio/transcriptions `
  -F "file=@tests/Input/ContactCenter/103046_1000780789-21-00-01.wav" `
  -F "model=parakeet-tdt-0.6b-v2" `
  -F "response_format=json"
```

### Text
```powershell
curl.exe -X POST http://localhost:8000/v1/audio/transcriptions `
  -F "file=@tests/Input/ContactCenter/103046_1000780789-21-00-01.wav" `
  -F "model=parakeet-tdt-0.6b-v2" `
  -F "response_format=text"
```

### SRT
```powershell
curl.exe -X POST http://localhost:8000/v1/audio/transcriptions `
  -F "file=@tests/Input/ContactCenter/103046_1000780789-21-00-01.wav" `
  -F "model=parakeet-tdt-0.6b-v2" `
  -F "response_format=srt"
```

### VTT
```powershell
curl.exe -X POST http://localhost:8000/v1/audio/transcriptions `
  -F "file=@tests/Input/ContactCenter/103046_1000780789-21-00-01.wav" `
  -F "model=parakeet-tdt-0.6b-v2" `
  -F "response_format=vtt"
```

### Verbose JSON
```powershell
curl.exe -X POST http://localhost:8000/v1/audio/transcriptions `
  -F "file=@tests/Input/ContactCenter/103046_1000780789-21-00-01.wav" `
  -F "model=parakeet-tdt-0.6b-v2" `
  -F "response_format=verbose_json"
```

---

## Saving Output to Files

### Save as JSON
```powershell
curl.exe -X POST http://localhost:8000/v1/audio/transcriptions `
  -F "file=@audio.wav" `
  -F "response_format=json" `
  -o output.json
```

### Save as SRT
```powershell
curl.exe -X POST http://localhost:8000/v1/audio/transcriptions `
  -F "file=@audio.wav" `
  -F "response_format=srt" `
  -o output.srt
```

### Save as VTT
```powershell
curl.exe -X POST http://localhost:8000/v1/audio/transcriptions `
  -F "file=@audio.wav" `
  -F "response_format=vtt" `
  -o output.vtt
```

### Save as Text
```powershell
curl.exe -X POST http://localhost:8000/v1/audio/transcriptions `
  -F "file=@audio.wav" `
  -F "response_format=text" `
  -o output.txt
```

---

## Format Selection Guide

**Choose JSON when**:
- Building API integrations
- Need metadata (duration, model info)
- Storing in databases
- Default choice for most applications

**Choose Text when**:
- Only need the transcription
- Minimal overhead required
- Copy-paste workflows
- Simple text processing

**Choose SRT when**:
- Creating video subtitles
- Need compatibility with media players
- Working with video editing software
- Standard subtitle format needed

**Choose VTT when**:
- Web-based video players
- HTML5 video elements
- Modern web applications
- Accessible web content

**Choose Verbose JSON when**:
- Need detailed segment information
- Building timeline visualizations
- Advanced text analysis
- Speaker tracking required
- Editing applications

---

## Notes

- All formats support speaker diarization when `diarize=true`
- Timestamps are automatically included in SRT, VTT, and verbose_json formats
- The `timestamps` parameter is only needed for JSON format to include segments
- All formats are compatible with the OpenAI Whisper API specification
