# LiveATC Stream Information

## How LiveATC Streams Work

LiveATC provides audio streams via simple HTTP URLs following this format:
```
http://d.liveatc.net/[mount_point]
```

## Current Stations

### KJFK - New York JFK Tower
- **Mount**: `kjfk_twr`
- **Frequency**: 123.900 MHz
- **Stream URL**: http://d.liveatc.net/kjfk_twr
- **PLS File**: https://www.liveatc.net/play/kjfk_twr.pls

### KLAX - Los Angeles Tower North
- **Mount**: `klax3`
- **Frequency**: 133.900 MHz
- **Stream URL**: http://d.liveatc.net/klax3
- **PLS File**: https://www.liveatc.net/play/klax3.pls

### KORD - Chicago O'Hare Tower North
- **Mount**: `kord1n2_twr_n`
- **Frequency**: 126.900 MHz
- **Stream URL**: http://d.liveatc.net/kord1n2_twr_n
- **PLS File**: https://www.liveatc.net/play/kord1n2_twr_n.pls

### CYYZ - Toronto Pearson Apron
- **Mount**: `cyyz9`
- **Frequency**: Apron
- **Stream URL**: http://d.liveatc.net/cyyz9
- **PLS File**: https://www.liveatc.net/play/cyyz9.pls

## CORS Proxy Solution

Since browsers block direct cross-origin audio streams, we implemented a backend proxy:

**Proxy Endpoint**: `GET /api/proxy/stream?url=[encoded_stream_url]`

**Example**:
```
http://localhost:3000/api/proxy/stream?url=http%3A%2F%2Fd.liveatc.net%2Fcyyz9
```

The proxy:
- Fetches the LiveATC stream server-side
- Adds proper CORS headers
- Streams the audio back to the frontend
- Supports indefinite streaming with 300s timeout

## Finding More Stations

1. Go to https://www.liveatc.net
2. Search for an airport (e.g., KJFK, KLAX)
3. Look for `.pls` file links (e.g., `kjfk_twr.pls`)
4. Remove the `.pls` extension to get the mount point
5. Use format: `http://d.liveatc.net/[mount_point]`

## Audio Format

- **Type**: Audio/MPEG (MP3)
- **Streaming**: Live, continuous
- **Bitrate**: Variable (typically 16-32 kbps)
