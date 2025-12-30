# ============================================
# 1. LOGIN
# ============================================
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Copy token from response, ex: 
# eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# ============================================
# 2. SET TOKEN (paste token copied)
# ============================================
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# ============================================
# 3. GET RECORDS
# ============================================
curl http://localhost:3000/api/records/get \
  -H "Authorization: Bearer $TOKEN"

# ============================================
# 4. GET CONFIGS
# ============================================
curl http://localhost:3000/api/configs/get \
  -H "Authorization: Bearer $TOKEN"

# ============================================
# 5. UPDATE CONFIGS
# ============================================
curl -X PUT http://localhost:3000/api/configs/update \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"thresholds":{"tilt_warning":15.0}}'

# ============================================
# 6. LOGOUT
# ============================================
curl -X POST http://localhost:3000/api/auth/logout \
  -H "Authorization: Bearer $TOKEN"