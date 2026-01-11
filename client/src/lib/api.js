// Use relative path in production, localhost in development
const API_BASE_URL = import.meta.env.MODE === 'production'
  ? '/api'
  : 'http://localhost:3000/api';

export async function getAtcStations() {
  const response = await fetch(`${API_BASE_URL}/atc-stations`);
  const data = await response.json();
  return data.data;
}

export async function getMusicSources() {
  const response = await fetch(`${API_BASE_URL}/music-sources`);
  const data = await response.json();
  return data.data;
}

export async function healthCheck() {
  const response = await fetch(`${API_BASE_URL}/health`);
  const data = await response.json();
  return data.success;
}

export async function extractYoutubeUrl(youtubeUrl) {
  const response = await fetch(
    `${API_BASE_URL}/youtube/extract?url=${encodeURIComponent(youtubeUrl)}`
  );
  const data = await response.json();
  return data.data;
}

export function getProxyUrl(streamUrl) {
  return `${API_BASE_URL}/proxy/stream?url=${encodeURIComponent(streamUrl)}`;
}

export function getMusicStreamUrl(sourceId) {
  return `${API_BASE_URL}/stream/music/${sourceId}`;
}
