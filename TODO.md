# 🚀 Emergency Dispatch System - Future Roadmap

## 📡 1. Real-Time Alerting (Zero-Refresh Dashboard)
- [ ] **Robust Redis Listener**: Implement a background task that auto-restarts the Redis subscription if it fails.
- [ ] **WebSocket Heartbeat**: Add a "ping/pong" mechanism and auto-reconnect logic to the React Frontend.
- [ ] **Toast Notifications**: Add browser-level pop-up alerts and distinct audio sirens for new accidents.
- [ ] **Simulation Feedback**: Ensure the `NEW_ACCIDENT` event triggers immediately after the AI Simulator finishes the 5s post-accident buffer.

## 🗄️ 2. Database & Production Scaling
- [ ] **Production Credentials**: Move DB credentials to an `.env` file (security).
- [ ] **Data Retention**: Add a cleanup script to archive/delete 30-day-old video clips to save disk space.
- [ ] **Role-Based Access**: Implement full JWT authentication for Super Admins vs Hospital Staff.

## 🚑 3. Mission Optimization
- [ ] **Historical Analytics**: Create a dashboard to show average response times and hospital admission speeds.
- [ ] **Multi-Unit Dispatch**: Allow the Command Center to assign multiple ambulances to "High" severity cases.
