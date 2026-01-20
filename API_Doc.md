# API Documentation 

## Base URL
```
http://localhost:3000
```

---

## 5.1. XÁC THỰC (Authentication)

### Login - Lấy token xác thực

**Endpoint:** `POST /api/auth/login`

**Request:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response (Success):**
```json
{
  "status": "success",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "message": "Login successful"
}
```

**Response (Failed):**
```json
{
  "error": "Invalid credentials"
}
```

**Default Accounts:**
- Admin: username=`admin`, password=`admin123`
- User: username=`user`, password=`user123`

---

### Logout - Vô hiệu hóa token

**Endpoint:** `POST /api/auth/logout`

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "status": "success",
  "message": "Logout successful"
}
```

---

## 5.2. GỬI VÀ LẤY DỮ LIỆU CẢM BIẾN

### Upload dữ liệu từ cảm biến (ESP32)

**Endpoint:** `POST coap://localhost:5683/api/records/upload`

**Protocol:** CoAP (UDP)

**Payload (JSON):**
```json
{
  "id": "ESP001",
  "ts": 1735123456789,
  "ax": 0.12,
  "ay": 0.05,
  "az": 9.81,
  "gx": 0.01,
  "gy": 0.02,
  "gz": 0.00,
  "mx": 25.5,
  "my": -12.3,
  "mz": 48.7,
  "tilt": 5.2,
  "lat": 21.0285,
  "lon": 105.8542
}
```

**Giải thích các trường:**
- `id`: Device ID
- `ts`: Timestamp (milliseconds, optional)
- `ax`, `ay`, `az`: Gia tốc tuyến tính (m/s²) - 3 giá trị
- `gx`, `gy`, `gz`: Góc xoay (rad/s) - 3 giá trị
- `mx`, `my`, `mz`: Hướng thiết bị/La bàn từ (µT) - 3 giá trị
- `tilt`: Góc nghiêng tính toán (độ)
- `lat`, `lon`: GPS (optional)

**Response:**
```json
{
  "status": "success",
  "severity": "normal",
  "message": "Bình thường - Không có nguy hiểm"
}
```

---

### Lấy dữ liệu cảm biến từ database

**Endpoint:** `GET /api/records/get`

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `device_id` (optional): ID thiết bị cụ thể
- `from` (optional): Timestamp bắt đầu (ISO 8601)
- `to` (optional): Timestamp kết thúc (ISO 8601)
- `limit` (optional): Số lượng records (default: 100)

**Examples:**
```
GET /api/records/get
GET /api/records/get?device_id=ESP001
GET /api/records/get?device_id=ESP001&limit=50
GET /api/records/get?device_id=ESP001&from=2025-12-28T00:00:00Z&to=2025-12-28T23:59:59Z
```

**Response:**
```json
[
  {
    "_id": {"$oid": "..."},
    "deviceId": "ESP001",
    "timestamp": {"$date": "2025-12-28T10:30:45.123Z"},
    "data": {
      "accel_x": 0.12,
      "accel_y": 0.05,
      "accel_z": 9.81,
      "gyro_x": 0.01,
      "gyro_y": 0.02,
      "gyro_z": 0.00,
      "mag_x": 25.5,
      "mag_y": -12.3,
      "mag_z": 48.7,
      "tilt_angle": 5.2
    },
    "severity": "normal",
    "location": {
      "lat": 21.0285,
      "lon": 105.8542
    }
  }
]
```

---

### Xóa dữ liệu cảm biến

**Endpoint:** `DELETE /api/records/delete`

**Headers:**
```
Authorization: Bearer <token>
```

**Yêu cầu:** Admin role

**Request Body:**
```json
{
  "device_id": "ESP001",
  "from": "2025-12-01T00:00:00Z",
  "to": "2025-12-28T23:59:59Z"
}
```

**Response:**
```json
{
  "status": "success",
  "deleted_count": 150
}
```

---

## 5.3. THAY ĐỔI CẤU HÌNH

### Lấy toàn bộ cấu hình

**Endpoint:** `GET /api/configs/get`

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "thresholds": {
    "tilt_warning": 10.0,
    "tilt_danger": 20.0,
    "tilt_critical": 30.0,
    "accel_warning": 10.5,
    "accel_danger": 12.0,
    "accel_critical": 15.0
  },
  "alert_settings": {
    "enable_email": false,
    "enable_sms": false,
    "enable_web_notification": true,
    "email_recipients": [],
    "sms_recipients": []
  },
  "sensor_settings": {
    "sample_rate": 5,
    "data_retention_days": 30
  },
  "display_settings": {
    "default_chart_range": "24h",
    "refresh_interval": 5
  }
}
```

---

### Reset cấu hình về mặc định

**Endpoint:** `POST /api/configs/reset`

**Headers:**
```
Authorization: Bearer <token>
```

**Yêu cầu:** Admin role

**Response:**
```json
{
  "status": "success",
  "message": "Configuration reset to defaults",
  "config": { ... }
}
```

---

### Cập nhật cấu hình

**Endpoint:** `PUT /api/configs/update`

**Headers:**
```
Authorization: Bearer <token>
```

**Yêu cầu:** Admin role

**Request Body (JSON):**
```json
{
  "thresholds": {
    "tilt_warning": 15.0,
    "tilt_critical": 35.0
  },
  "alert_settings": {
    "enable_email": true,
    "email_recipients": ["admin@example.com"]
  }
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Configuration updated",
  "config": { ... }
}
```

---

## CÁC API BỔ SUNG (Tương thích)

### Health Check

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "ok",
  "mongodb": "connected",
  "coap": "running",
  "timestamp": "2025-12-28T10:30:45.123Z"
}
```

---

### Lấy dữ liệu mới nhất tất cả thiết bị

**Endpoint:** `GET /api/devices/latest`

**Headers:**
```
Authorization: Bearer <token>
```

---

### Lấy lịch sử thiết bị

**Endpoint:** `GET /api/devices/{device_id}/history`

**Headers:**
```
Authorization: Bearer <token>
```

---

### Lấy danh sách cảnh báo

**Endpoint:** `GET /api/alerts`

**Headers:**
```
Authorization: Bearer <token>
```

---

### Lấy thống kê

**Endpoint:** `GET /api/statistics`

**Headers:**
```
Authorization: Bearer <token>
```

---

## Authentication Flow

```
1. Client gọi POST /api/auth/login với username/password
2. Server trả về token (JWT)
3. Client lưu token
4. Mỗi request tiếp theo, client gửi token trong header:
   Authorization: Bearer <token>
5. Server verify token và xử lý request
6. Khi logout, gọi POST /api/auth/logout để vô hiệu hóa token
```

---

## Error Codes

| Code | Ý nghĩa |
|------|---------|
| 200 | Success |
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Token không hợp lệ hoặc chưa login |
| 403 | Forbidden - Không đủ quyền (cần Admin) |
| 404 | Not Found - Endpoint không tồn tại |
| 500 | Internal Server Error |

---

## Testing với curl

### Login
```bash
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

### Get records với token
```bash
TOKEN="your-token-here"
curl -X GET http://localhost:3000/api/records/get \
  -H "Authorization: Bearer $TOKEN"
```

### Update config
```bash
curl -X PUT http://localhost:3000/api/configs/update \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"thresholds":{"tilt_warning":15.0}}'
```

---

## Testing với CoAP

```bash
# Install coap client
pip install aiocoap[all]

# Send test data
echo '{"id":"ESP001","ax":0.1,"ay":0.05,"az":9.8,"gx":0,"gy":0,"gz":0,"mx":25,"my":-12,"mz":48,"tilt":5.2}' | \
aiocoap-client -m POST coap://localhost:5683/api/records/upload
```