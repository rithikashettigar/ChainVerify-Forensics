# Intelligent Media Forensics

## Overview

Intelligent Media Forensics is a comprehensive digital integrity verification system designed to detect and analyze tampering in digital images and videos.  
The system uses Blockchain-secured SHA-256 hashing to guarantee immutability and forensic traceability, enabling detection of even minimal visual manipulation.

NOTE: This project does NOT have a live demo. It is intended to be executed locally.

---

## Features

### Blockchain-Secured Integrity
- SHA-256 based cryptographic fingerprinting
- Hashes stored in immutable blockchain ledgers
- Prevents retroactive manipulation

### On-Demand Video Reconstruction
- Heavy video processing is executed only on request
- Optimizes system performance and memory usage

### Dual-Mode Forensic Analysis
- Static image tamper detection
- Frame-level video integrity verification

### Automated User Auditing
- All user login activities are recorded
- Logs stored in registry directory

### Dynamic Dashboard
- Clearly displays authentic vs tampered media
- Shows integrity status and block alteration percentage

---

## Prerequisites

- Python 3.x
- Flask Framework
- OpenCV
- Pillow (PIL)
- SQLite (db.py)

Install dependencies:
```bash
pip install -r requirements.txt
```

---

## How It Works

### 1. SHA-256 Hashing
- Media files are hashed during registration
- Hash uniquely represents media content

### 2. Blockchain Verification
- Hash stored in blockchain.json / ledger.json
- Uploaded files are re-hashed and compared

### 3. Frame-Level Video Analysis
- Videos are split into frames
- Each frame is hashed independently
- Tampered frames are precisely detected

### 4. Reconstruction Logic
- Hash mismatch flags media as TAMPERED
- Verified blocks are used to reconstruct original media

---

## How to Use

### Step 1: Setup

pip install -r requirements.txt


### Step 2: Run Application

python app.py


### Step 3: Register Media
- Upload original image or video
- Baseline hash stored on blockchain

### Step 4: Verify Media
- Upload suspicious file
- Integrity status and tampering percentage displayed

### Step 5: Reconstruct Media (Videos)
- Click "Generate Reconstructed Video" if tampered

---

## Example Usage

1. User logs in
   -> Login recorded

2. Verify media
   -> File: temp.mp4
   -> Reference ID: VDIO001

3. Result
   -> Integrity Compromised
   -> Blocks Altered: 100%

4. Action
   -> Generate Reconstructed Video



---

## Project Structure



## Project Structure

```text
IMAGE_INTEGRITY_SYSTEM/
├── app.py
├── config.py
├── db.py
├── register.py
├── requirements.txt
├── users.db
│
├── core/
│   ├── hashing.py
│   ├── merkle.py
│   ├── preprocess.py
│   ├── recovery.py
│   ├── registry.py
│   ├── storage.py
│   └── verify.py
│
├── core_video/
│   ├── extract_frames.py
│   ├── frame_hashing.py
│   ├── video_merkle.py
│   ├── video_reconstruction.py
│   ├── video_recovery.py
│   └── video_verify.py
│
├── services/
│   ├── image_register_service.py
│   ├── image_verify_service.py
│   ├── video_register_service.py
│   └── video_verify_service.py
│
├── registry/
│   ├── blockchain.json
│   └── ledger.json
│
├── storage/
│   ├── blocks/
│   ├── ipfs/
│   └── video_frames/
│
├── reconstructed/
│
├── outputs/
│   ├── images/
│   └── recovered_video/
│
├── uploads/
│   ├── images/
│   └── videos/
│
├── templates/
│   ├── dashboard.html
│   ├── login.html
│   └── signup.html
│
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
│
└── venv/

```
---

## Notes

- Console logs assist in debugging server errors
- Media uploads are segregated for clarity
- Clean UI with professional forensic layout

---

## Future Enhancements

- Deep learning based manipulation detection
- IPFS decentralized storage integration
- Real-time integrity alert system

---

## Contribution

Contributions are welcome.  
Feel free to open issues or submit pull requests.

---

## Author

GitHub: @Ragha8951  
Email: ragha8951@gmail.com

---

Thank you for visiting ❤️




