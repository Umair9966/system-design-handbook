# Live Video Streaming Architecture: HLS, DASH, and WebRTC

Live video distribution spans a strict trade-off between **ultra-low latency** (interactive bidding, gaming) and **massive global scale** (World Cup, Super Bowl).

```mermaid
graph LR
    Source[Camera / Video Feed] --> Encoder[Hardware Encoder / RTMP]
    Encoder --> Transcoder[Transcoding Service: Multi-bitrate H.264/AV1 Chunks]
    Transcoder --> Packager[Packager: HLS (.m3u8 + .ts) / DASH (.mpd + .m4s)]
    Packager --> S3[(Origin Storage / S3)]
    S3 --> CDN[Global CDN Edge: Cloudflare / Akamai]
    CDN --> Viewer1[Viewer Browser (HLS: 6s Latency)]
    CDN --> Viewer2[Viewer TV / Mobile]
```

---

## 1. Comparing Video Streaming Protocols

| Protocol | Transport | Latency | Scalability | Use Case |
| :--- | :--- | :--- | :--- | :--- |
| **WebRTC** | UDP (RTP/RTCP) | < 500ms (Sub-second) | Low to Moderate (Expensive peer/relay servers) | Zoom, Google Meet, live auctions, tele-health |
| **Low-Latency HLS (LL-HLS)**| HTTP/2 or HTTP/3 | 1.5s - 3s | High (Standard CDN chunk caching) | Twitch, live sports, live concerts |
| **Standard HLS / DASH** | HTTP/1.1 or HTTP/2 | 6s - 30s | Massive (Millions of viewers via edge CDNs) | Netflix, YouTube Live, broadcast sports |

---

## 2. Adaptive Bitrate Streaming (ABR)

Network bandwidth on mobile devices fluctuates continuously. ABR dynamically adjusts video quality without playback stalling:

```mermaid
graph TD
    Client[Video Player Client] --> Monitor[Bandwidth Estimator]
    Monitor -->|Bandwidth = 15 Mbps| High[Download 1080p Chunk (4 Mbps)]
    Monitor -->|Cellular Drops to 2 Mbps| Med[Download 720p Chunk (1.5 Mbps)]
    Monitor -->|Subway Tunnel: 500 Kbps| Low[Download 360p Chunk (300 Kbps)]
    Note over Client: Video plays continuously with ZERO buffering spinners!
```

---

## 3. Key Takeaways

- Use WebRTC for two-way sub-second interactive video (Zoom, Discord voice).
- Use HLS or DASH for one-to-many broadcast streaming to leverage commodity CDN edge caching.
- Generate multi-bitrate profiles (ABR) during packaging to ensure continuous playback across changing client bandwidth.
