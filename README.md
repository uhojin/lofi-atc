# Lofi ATC Radio

A web application that streams lofi music from various sources mixed with real air traffic control (ATC) radio audio from LiveATC.net.

## Features

- 🎵 **Multi-Source Music Streaming**:
  - YouTube live streams (Lofi Girl, College Music, Synthwave Radio)
  - Automatic stream URL extraction via yt-dlp
  - Future: Spotify, SoundCloud, custom sources
- 📻 **Real ATC Radio**: Live audio from LiveATC.net
  - JFK Tower (New York)
  - LAX Tower North (Los Angeles)
  - ORD Tower North (Chicago O'Hare)
  - CYYZ Apron (Toronto Pearson)
- 🔀 **Seamless Switching**: Change ATC stations and music sources on the fly
- 🎛️ **Independent Volume Controls**: Mix ATC and music to your preference
- ⚡ **High Performance**: Rust backend with efficient stream proxying
- 🎨 **Retro ATC Aesthetic**: Retro UI inspired by pixel designs

## Architecture

### Frontend (Svelte + Web Audio API)
- Client-side audio mixing using Web Audio API
- Dual-track audio engine (ATC + Music)
- Independent gain control for each source
- Smooth crossfading between sources

### Backend (Rust + Axum + Tokio)
- **Stream Proxying**: Handles CORS and provides unified audio interface
- **YouTube Extraction**: Uses yt-dlp to extract direct stream URLs
- **LiveATC Integration**: Direct streaming from LiveATC feeds
- Async HTTP with long-lived connections for streaming

## Project Structure

```
lofi-atc/
├── client/                    # Svelte frontend
│   ├── src/
│   │   ├── lib/
│   │   │   ├── audio/
│   │   │   │   └── audioEngine.js    # Web Audio API engine
│   │   │   ├── components/           # Svelte components
│   │   │   └── api.js                # Backend API client
│   │   ├── App.svelte                # Main app
│   │   └── main.js
│   └── package.json
├── server/                    # Rust backend
│   ├── src/
│   │   └── main.rs                   # API server
│   └── Cargo.toml
├── STREAMS.md                 # LiveATC stream documentation
└── README.md
```

## Getting Started

### Prerequisites

- **Node.js 20+** (for frontend)
- **Rust 1.70+** (for backend)
- **yt-dlp** (for YouTube extraction)
  ```bash
  # macOS
  brew install yt-dlp

  # Linux
  pip install yt-dlp

  # Or download from https://github.com/yt-dlp/yt-dlp
  ```

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd lofi-atc
   ```

2. **Backend Setup**
   ```bash
   cd server
   cargo build
   cargo run
   ```
   Backend will start on `http://localhost:3000`

3. **Frontend Setup** (in a new terminal)
   ```bash
   cd client
   npm install
   npm run dev
   ```
   Frontend will start on `http://localhost:5173`

4. **Open in browser**
   Navigate to http://localhost:5173

## How It Works

### Audio Mixing
All audio mixing happens **client-side** using the Web Audio API:
1. Two separate audio sources (ATC + Music) are created
2. Each connects to its own GainNode for volume control
3. Both mix through a master GainNode before output
4. This allows independent volume control and smooth crossfading

### Stream Proxying
The backend handles CORS and stream extraction:
- **LiveATC**: Direct proxy of `http://d.liveatc.net/*` streams
- **YouTube**:
  1. Extract direct stream URL using yt-dlp
  2. Proxy the extracted URL to avoid CORS issues
  3. Return audio stream to frontend

### API Endpoints
- `GET /api/health` - Health check
- `GET /api/atc-stations` - List available ATC stations
- `GET /api/music-sources` - List available music sources
- `GET /api/proxy/stream?url=<url>` - Proxy an audio stream
- `GET /api/youtube/extract?url=<url>` - Extract YouTube stream URL

## Usage

1. **Select an ATC Station**: Click on any airport (KJFK, KLAX, KORD, CYYZ)
2. **Select Music Source**: Choose from Lofi Girl streams or synthwave radio
3. **Adjust Volumes**: Use sliders to balance ATC and music levels
4. **Switch Sources**: Change stations or music anytime with smooth transitions

## Development

### Run in Development Mode
```bash
# Terminal 1 - Backend
cd server && cargo run

# Terminal 2 - Frontend
cd client && npm run dev
```

### Production Build
```bash
# Backend
cd server && cargo build --release

# Frontend
cd client && npm run build
```

## Technical Details

- **Audio Format**: MP3 streams
- **Streaming Protocol**: HTTP with chunked transfer
- **Concurrent Streams**: 2 (ATC + Music)
- **Timeout**: 300s for long-lived connections
- **CORS**: Fully handled by backend proxy

## Future Enhancements

- [ ] Spotify integration
- [ ] SoundCloud integration
- [ ] Custom audio source upload
- [ ] Audio visualization (spectrum analyzer)
- [ ] Playlist/favorites system
- [ ] Mobile-responsive design
- [ ] Keyboard shortcuts
- [ ] Preset mixer configurations

## License

MIT
