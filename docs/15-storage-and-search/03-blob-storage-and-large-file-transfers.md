# Blob Storage and Large File Transfers

Uploading and serving massive files (gigabytes to terabytes, such as 4K videos or database backups) requires specialized streaming, multipart chunking, and presigned security patterns.

```mermaid
sequenceDiagram
    autonumber
    participant Client as Client Browser / Mobile
    participant API as Backend API Server
    participant S3 as AWS S3 / Object Store

    Client->>API: POST /upload/initiate { filename: "movie.mp4", size: 5GB }
    API->>S3: InitiateMultipartUpload
    S3-->>API: Returns UploadID
    API->>S3: GeneratePresignedUploadURLs(UploadID, Chunks: 1000)
    API-->>Client: Returns Presigned S3 URLs for each 5MB chunk
    
    par Parallel Direct Chunk Upload (Bypasses Backend API!)
        Client->>S3: PUT chunk_1 to Presigned URL 1
        Client->>S3: PUT chunk_2 to Presigned URL 2
        Client->>S3: PUT chunk_N to Presigned URL N
    end
    
    Client->>API: POST /upload/complete { UploadID, ETags: [...] }
    API->>S3: CompleteMultipartUpload(UploadID, ETags)
    S3-->>API: 200 OK (Object Assembled)
    API-->>Client: Upload Successful!
```

---

## 1. Direct-to-Storage with Presigned URLs

### The Anti-Pattern:
Uploading files through your application backend servers saturates backend network bandwidth, exhausts worker threads, and risks connection timeouts on slow mobile networks.

### The Best Practice:
Generate short-lived (15-minute) **Presigned URLs** with cryptographic signatures. The client uploads data **directly to object storage (S3)**, completely bypassing your application servers.

---

## 2. Multipart Upload Mechanics

For files larger than 100MB, multipart uploads are mandatory:
1. **Parallelism**: Chunks (typically 5MB - 20MB) upload in parallel across multiple TCP sockets, saturating client bandwidth.
2. **Resumability**: If chunk 47 fails due to network drop, only chunk 47 is retried—not the entire 5GB file.
3. **Pipelining**: Uploading can begin while the file is still being generated or recorded on the client device.

---

## 3. Key Takeaways

- Never stream large file uploads or downloads through application backend memory; always use direct-to-storage Presigned URLs.
- Always use Multipart Uploads for files $> 100	ext{MB}$ to support parallel chunking and granular retry.
- Front public blob downloads with a Content Delivery Network (CDN) to cache static media close to users.
