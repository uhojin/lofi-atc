use axum::{
    body::Body,
    extract::{Path, Query},
    http::{header, HeaderMap, StatusCode},
    response::{IntoResponse, Json, Response},
    routing::get,
    Router,
};
use serde::{Deserialize, Serialize};
use std::net::SocketAddr;
use std::process::{Command, Stdio};
use tokio::process::Command as TokioCommand;
use tokio_util::io::ReaderStream;
use tower_http::cors::{CorsLayer, Any};
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

#[derive(Debug, Serialize, Deserialize, Clone)]
struct AtcStation {
    id: String,
    name: String,
    airport_code: String,
    frequency: String,
    description: String,
    stream_url: String,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
struct MusicSource {
    id: String,
    name: String,
    source_type: String,
    stream_url: String,
    thumbnail: Option<String>,
}

#[derive(Debug, Serialize)]
struct ApiResponse<T> {
    success: bool,
    data: T,
}

#[derive(Debug, Deserialize)]
struct ProxyQuery {
    url: String,
}

#[derive(Debug, Serialize)]
struct YoutubeStreamInfo {
    stream_url: String,
    title: String,
}

#[tokio::main]
async fn main() {
    tracing_subscriber::registry()
        .with(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "lofi_atc_server=debug,tower_http=debug,axum=trace".into()),
        )
        .with(tracing_subscriber::fmt::layer())
        .init();

    let cors = CorsLayer::new()
        .allow_origin(Any)
        .allow_methods(Any)
        .allow_headers(Any);

    let app = Router::new()
        .route("/", get(health_check))
        .route("/api/health", get(health_check))
        .route("/api/atc-stations", get(get_atc_stations))
        .route("/api/music-sources", get(get_music_sources))
        .route("/api/proxy/stream", get(proxy_stream))
        .route("/api/youtube/extract", get(extract_youtube_url))
        .route("/api/stream/music/:source_id", get(stream_music))
        .layer(cors);

    let addr = SocketAddr::from(([127, 0, 0, 1], 3000));
    tracing::info!("Lofi ATC Server listening on {}", addr);

    let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
    axum::serve(listener, app).await.unwrap();
}

async fn health_check() -> Json<ApiResponse<String>> {
    Json(ApiResponse {
        success: true,
        data: "Lofi ATC Server is running".to_string(),
    })
}

async fn get_atc_stations() -> Json<ApiResponse<Vec<AtcStation>>> {
    let stations = vec![
        AtcStation {
            id: "kjfk_twr".to_string(),
            name: "JFK Tower".to_string(),
            airport_code: "KJFK".to_string(),
            frequency: "123.900".to_string(),
            description: "New York JFK Tower".to_string(),
            stream_url: "http://d.liveatc.net/kjfk_twr".to_string(),
        },
        AtcStation {
            id: "klax3".to_string(),
            name: "LAX Tower North".to_string(),
            airport_code: "KLAX".to_string(),
            frequency: "133.900".to_string(),
            description: "Los Angeles Tower North".to_string(),
            stream_url: "http://d.liveatc.net/klax3".to_string(),
        },
        AtcStation {
            id: "kord1n2_twr_n".to_string(),
            name: "ORD Tower North".to_string(),
            airport_code: "KORD".to_string(),
            frequency: "126.900".to_string(),
            description: "Chicago O'Hare Tower North".to_string(),
            stream_url: "http://d.liveatc.net/kord1n2_twr_n".to_string(),
        },
        AtcStation {
            id: "cyyz9".to_string(),
            name: "Toronto Pearson Apron".to_string(),
            airport_code: "CYYZ".to_string(),
            frequency: "Apron".to_string(),
            description: "Toronto Pearson Apron".to_string(),
            stream_url: "http://d.liveatc.net/cyyz9".to_string(),
        },
    ];

    Json(ApiResponse {
        success: true,
        data: stations,
    })
}

async fn get_music_sources() -> Json<ApiResponse<Vec<MusicSource>>> {
    let sources = vec![
        MusicSource {
            id: "lofi_girl".to_string(),
            name: "Lofi Girl - beats to relax/study to".to_string(),
            source_type: "youtube".to_string(),
            stream_url: "https://www.youtube.com/watch?v=jfKfPfyJRdk".to_string(),
            thumbnail: Some("https://i.ytimg.com/vi/jfKfPfyJRdk/maxresdefault.jpg".to_string()),
        },
        MusicSource {
            id: "lofi_girl_sleep".to_string(),
            name: "Lofi Girl - beats to sleep/chill to".to_string(),
            source_type: "youtube".to_string(),
            stream_url: "https://www.youtube.com/watch?v=rUxyKA_-grg".to_string(),
            thumbnail: Some("https://i.ytimg.com/vi/rUxyKA_-grg/maxresdefault.jpg".to_string()),
        },
        MusicSource {
            id: "lofi_girl_synthwave".to_string(),
            name: "Lofi Girl - synthwave radio".to_string(),
            source_type: "youtube".to_string(),
            stream_url: "https://www.youtube.com/watch?v=4xDzrJKXOOY".to_string(),
            thumbnail: Some("https://i.ytimg.com/vi/4xDzrJKXOOY/maxresdefault.jpg".to_string()),
        },
        MusicSource {
            id: "college_music".to_string(),
            name: "College Music - lofi hip hop radio".to_string(),
            source_type: "youtube".to_string(),
            stream_url: "https://www.youtube.com/watch?v=7NOSDKb0HlU".to_string(),
            thumbnail: Some("https://i.ytimg.com/vi/7NOSDKb0HlU/maxresdefault.jpg".to_string()),
        },
    ];

    Json(ApiResponse {
        success: true,
        data: sources,
    })
}

async fn proxy_stream(Query(params): Query<ProxyQuery>) -> Response {
    let stream_url = params.url.clone();

    tracing::info!("Proxying stream from: {}", stream_url);

    let client = reqwest::Client::new();

    match client.get(&stream_url).send().await {
        Ok(response) => {
            let is_manifest = stream_url.contains(".m3u8") || stream_url.contains("/manifest/");

            if is_manifest {
                match response.text().await {
                    Ok(manifest_content) => {
                        let rewritten_manifest = rewrite_m3u8_manifest(&manifest_content, &stream_url);

                        let mut headers = HeaderMap::new();
                        headers.insert(header::CONTENT_TYPE, "application/vnd.apple.mpegurl".parse().unwrap());
                        headers.insert(header::CACHE_CONTROL, "no-cache".parse().unwrap());
                        headers.insert(header::ACCESS_CONTROL_ALLOW_ORIGIN, "*".parse().unwrap());

                        (headers, rewritten_manifest).into_response()
                    }
                    Err(e) => {
                        tracing::error!("Failed to read HLS manifest: {}", e);
                        (StatusCode::INTERNAL_SERVER_ERROR, "Failed to read HLS manifest").into_response()
                    }
                }
            } else {
                let original_content_type = response
                    .headers()
                    .get(header::CONTENT_TYPE)
                    .and_then(|v| v.to_str().ok())
                    .unwrap_or("application/octet-stream");

                tracing::debug!("Proxying binary stream, Content-Type: {} for URL: {}", original_content_type, &stream_url);

                let mut headers = HeaderMap::new();
                headers.insert(header::CONTENT_TYPE, original_content_type.parse().unwrap());
                headers.insert(header::CACHE_CONTROL, "no-cache".parse().unwrap());
                headers.insert(header::ACCESS_CONTROL_ALLOW_ORIGIN, "*".parse().unwrap());
                headers.insert(header::ACCESS_CONTROL_EXPOSE_HEADERS, "*".parse().unwrap());

                if let Some(content_length) = response.headers().get(header::CONTENT_LENGTH) {
                    headers.insert(header::CONTENT_LENGTH, content_length.clone());
                }

                let stream = response.bytes_stream();
                let body = Body::from_stream(stream);

                (headers, body).into_response()
            }
        }
        Err(e) => {
            tracing::error!("Failed to proxy stream: {}", e);
            (
                StatusCode::BAD_GATEWAY,
                format!("Failed to connect to stream: {}", e),
            )
                .into_response()
        }
    }
}

fn rewrite_m3u8_manifest(manifest: &str, base_url: &str) -> String {
    let mut result = String::new();
    let base_url_parsed = url::Url::parse(base_url).ok();

    for line in manifest.lines() {
        if line.starts_with("#") || line.trim().is_empty() {
            result.push_str(line);
            result.push('\n');
        } else if line.starts_with("http://") || line.starts_with("https://") {
            let proxied_url = format!("http://localhost:3000/api/proxy/stream?url={}",
                urlencoding::encode(line));
            result.push_str(&proxied_url);
            result.push('\n');
        } else {
            if let Some(base) = &base_url_parsed {
                if let Ok(resolved) = base.join(line) {
                    let proxied_url = format!("http://localhost:3000/api/proxy/stream?url={}",
                        urlencoding::encode(resolved.as_str()));
                    result.push_str(&proxied_url);
                    result.push('\n');
                } else {
                    result.push_str(line);
                    result.push('\n');
                }
            } else {
                result.push_str(line);
                result.push('\n');
            }
        }
    }

    result
}

async fn extract_youtube_url(Query(params): Query<ProxyQuery>) -> Response {
    let youtube_url = params.url;

    tracing::info!("Extracting stream URL from YouTube: {}", youtube_url);

    let output = Command::new("yt-dlp")
        .args(&[
            "-f", "ba/b",
            "--get-url",
            "--get-title",
            &youtube_url,
        ])
        .output();

    match output {
        Ok(result) => {
            if result.status.success() {
                let output_str = String::from_utf8_lossy(&result.stdout);
                let lines: Vec<&str> = output_str.trim().split('\n').collect();

                if lines.len() >= 2 {
                    let title = lines[0].to_string();
                    let stream_url = lines[1].to_string();

                    let info = YoutubeStreamInfo {
                        stream_url,
                        title,
                    };

                    tracing::info!("Successfully extracted YouTube stream: {}", info.title);

                    Json(ApiResponse {
                        success: true,
                        data: info,
                    }).into_response()
                } else {
                    tracing::error!("Unexpected yt-dlp output format");
                    (
                        StatusCode::INTERNAL_SERVER_ERROR,
                        "Failed to parse yt-dlp output",
                    ).into_response()
                }
            } else {
                let error_msg = String::from_utf8_lossy(&result.stderr);
                tracing::error!("yt-dlp failed: {}", error_msg);
                (
                    StatusCode::INTERNAL_SERVER_ERROR,
                    format!("Failed to extract YouTube URL: {}", error_msg),
                ).into_response()
            }
        }
        Err(e) => {
            tracing::error!("Failed to execute yt-dlp: {}", e);
            (
                StatusCode::INTERNAL_SERVER_ERROR,
                "Failed to execute yt-dlp. Make sure it's installed.",
            ).into_response()
        }
    }
}

async fn stream_music(Path(source_id): Path<String>) -> Response {
    tracing::info!("Streaming music for source: {}", source_id);

    // Get music sources (same as get_music_sources)
    let sources = vec![
        MusicSource {
            id: "lofi_girl".to_string(),
            name: "Lofi Girl - beats to relax/study to".to_string(),
            source_type: "youtube".to_string(),
            stream_url: "https://www.youtube.com/watch?v=jfKfPfyJRdk".to_string(),
            thumbnail: Some("https://i.ytimg.com/vi/jfKfPfyJRdk/maxresdefault.jpg".to_string()),
        },
        MusicSource {
            id: "lofi_girl_sleep".to_string(),
            name: "Lofi Girl - beats to sleep/chill to".to_string(),
            source_type: "youtube".to_string(),
            stream_url: "https://www.youtube.com/watch?v=rUxyKA_-grg".to_string(),
            thumbnail: Some("https://i.ytimg.com/vi/rUxyKA_-grg/maxresdefault.jpg".to_string()),
        },
        MusicSource {
            id: "lofi_girl_synthwave".to_string(),
            name: "Lofi Girl - synthwave radio".to_string(),
            source_type: "youtube".to_string(),
            stream_url: "https://www.youtube.com/watch?v=4xDzrJKXOOY".to_string(),
            thumbnail: Some("https://i.ytimg.com/vi/4xDzrJKXOOY/maxresdefault.jpg".to_string()),
        },
        MusicSource {
            id: "college_music".to_string(),
            name: "College Music - lofi hip hop radio".to_string(),
            source_type: "youtube".to_string(),
            stream_url: "https://www.youtube.com/watch?v=7NOSDKb0HlU".to_string(),
            thumbnail: Some("https://i.ytimg.com/vi/7NOSDKb0HlU/maxresdefault.jpg".to_string()),
        },
    ];

    // Find the requested source
    let source = sources.iter().find(|s| s.id == source_id);

    if source.is_none() {
        return (StatusCode::NOT_FOUND, "Music source not found").into_response();
    }

    let source = source.unwrap();
    let youtube_url = &source.stream_url;

    tracing::info!("Starting ffmpeg pipeline for: {}", youtube_url);

    // Use shell to pipe yt-dlp to ffmpeg
    // yt-dlp -f ba -o - [url] | ffmpeg -i pipe:0 -f mp3 -b:a 128k -vn pipe:1
    let command = format!(
        "yt-dlp -f 'ba/b' -o - '{}' 2>/dev/null | ffmpeg -i pipe:0 -f mp3 -b:a 128k -vn -loglevel error pipe:1",
        youtube_url
    );

    let mut child = match TokioCommand::new("sh")
        .arg("-c")
        .arg(&command)
        .stdout(Stdio::piped())
        .stderr(Stdio::null())
        .spawn()
    {
        Ok(child) => child,
        Err(e) => {
            tracing::error!("Failed to spawn streaming pipeline: {}", e);
            return (
                StatusCode::INTERNAL_SERVER_ERROR,
                "Failed to start streaming pipeline",
            ).into_response();
        }
    };

    let stdout = child.stdout.take().unwrap();
    let stream = ReaderStream::new(stdout);
    let body = Body::from_stream(stream);

    // Spawn cleanup task
    let cleanup_source_id = source_id.clone();
    tokio::spawn(async move {
        let _ = child.wait().await;
        tracing::info!("Cleaned up streaming process for source: {}", cleanup_source_id);
    });

    let mut headers = HeaderMap::new();
    headers.insert(header::CONTENT_TYPE, "audio/mpeg".parse().unwrap());
    headers.insert(header::CACHE_CONTROL, "no-cache".parse().unwrap());
    headers.insert(header::ACCESS_CONTROL_ALLOW_ORIGIN, "*".parse().unwrap());

    (headers, body).into_response()
}
