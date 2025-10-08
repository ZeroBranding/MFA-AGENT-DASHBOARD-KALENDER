# 📋 PHASE 2: ARCHITEKTUR-OPTIMIERUNG

**Start:** Nach Phase 1 Testing  
**Dauer:** 2-3 Tage  
**Ziel:** Production-Grade Architektur  
**Perspektive:** Senior System-Architect

---

## 🎯 STRATEGIC GOALS

### **Hauptziele:**
1. **Contexts auf Backend umstellen** - Echte State-Management
2. **Offline-First-Strategie** - Funktioniert ohne Internet
3. **Performance-Optimierung** - Bundle-Size, Lazy-Loading
4. **Security-Hardening** - Production-Security

---

## 📋 DETAILED TODO-LIST

### **2.1 Contexts → Backend Migration**

#### **2.1.1 EmailContext umbauen**
**Aktuell:** localStorage  
**Neu:** Backend-API mit Sync

**Tasks:**
- [ ] `useEmail()` Hook auf `useBackendData()` umstellen
- [ ] Emails von `/api/emails` laden
- [ ] `addEmail()` → POST `/api/emails`
- [ ] `updateEmail()` → PUT `/api/emails/{id}`
- [ ] `deleteEmail()` → DELETE `/api/emails/{id}`
- [ ] Optimistic Updates mit React Query
- [ ] Offline-Queue für Failed Requests
- [ ] localStorage nur als Cache

**Dateien:**
- `src/contexts/EmailContext.tsx` (komplett umbauen)

**Impact:** Echte E-Mail-Daten, Multi-Tab-Sync

---

#### **2.1.2 AgentContext umbauen**
**Aktuell:** Simuliert  
**Neu:** Echte Backend-Daten

**Tasks:**
- [ ] Agent-Status von `/api/stats` holen
- [ ] `startAgent()` → POST `/api/agent/start`
- [ ] `stopAgent()` → POST `/api/agent/stop`
- [ ] Agent-Logs von Backend holen (neuer Endpoint?)
- [ ] Performance-Stats von `/api/performance`
- [ ] WebSocket für Live-Updates

**Dateien:**
- `src/contexts/AgentContext.tsx` (umbauen)
- `MFA/api/dashboard_api.py` (Agent-Logs-Endpoint hinzufügen)

**Impact:** Echte Agent-Kontrolle

---

#### **2.1.3 PracticeContext optimieren**
**Aktuell:** localStorage  
**Neu:** Backend + localStorage-Sync

**Tasks:**
- [ ] Practice-Data von `/api/settings` holen
- [ ] `updatePracticeData()` → PUT `/api/settings`
- [ ] Audit-Log auf Backend speichern (neuer Endpoint?)
- [ ] Session-Management auf Backend
- [ ] Multi-User-Support vorbereiten

**Dateien:**
- `src/contexts/PracticeContext.tsx` (erweitern)
- `MFA/api/dashboard_api.py` (Audit-Log-Endpoint)

**Impact:** Zentrale Settings-Verwaltung

---

### **2.2 Offline-First-Strategie**

#### **2.2.1 Service Worker Setup**
**Tasks:**
- [ ] Vite PWA Plugin installieren
- [ ] Service Worker konfigurieren
- [ ] Cache-Strategie definieren
- [ ] Offline-Fallback-Seite

**Code:**
```bash
npm install vite-plugin-pwa
```

```typescript
// vite.config.ts
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg}'],
        runtimeCaching: [
          {
            urlPattern: /^http:\/\/localhost:5000\/api\/.*/i,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-cache',
              expiration: {
                maxEntries: 100,
                maxAgeSeconds: 60 * 5 // 5 Minuten
              }
            }
          }
        ]
      }
    })
  ]
})
```

**Impact:** App funktioniert offline

---

#### **2.2.2 Offline-Sync-Queue**
**Tasks:**
- [ ] IndexedDB für Offline-Storage
- [ ] Sync-Queue für Failed Requests
- [ ] Automatic Retry bei Reconnect
- [ ] Conflict-Resolution

**Code:**
```typescript
// src/lib/offline-sync.ts
class OfflineSync {
  private db: IDBDatabase;
  private queue: SyncItem[] = [];
  
  async addToQueue(item: SyncItem) {
    await this.db.add('sync_queue', item);
    this.queue.push(item);
  }
  
  async processQueue() {
    for (const item of this.queue) {
      try {
        await this.syncItem(item);
        await this.db.delete('sync_queue', item.id);
      } catch (error) {
        // Retry later
      }
    }
  }
}
```

**Impact:** Keine Datenverluste

---

### **2.3 Performance-Optimierung**

#### **2.3.1 Code-Splitting**
**Tasks:**
- [ ] React.lazy() für alle Pages
- [ ] Suspense-Boundaries
- [ ] Route-based Splitting
- [ ] Component-Preloading

**Code:**
```typescript
// src/App.tsx
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Inbox = lazy(() => import('./pages/Inbox'));
const Reports = lazy(() => import('./pages/Reports'));

// Wrapping
<Suspense fallback={<LoadingSpinner />}>
  <Dashboard />
</Suspense>
```

**Impact:** -60% Initial Bundle-Size

---

#### **2.3.2 Image-Optimierung**
**Tasks:**
- [ ] Vite Image-Plugin
- [ ] WebP-Conversion
- [ ] Lazy-Loading für Images
- [ ] Responsive Images

**Impact:** -40% Image-Size

---

#### **2.3.3 Bundle-Analyse**
**Tasks:**
- [ ] rollup-plugin-visualizer installieren
- [ ] Bundle-Size analysieren
- [ ] Tree-Shaking optimieren
- [ ] Unused Imports entfernen

**Code:**
```bash
npm install --save-dev rollup-plugin-visualizer
npm run build
# stats.html zeigt Bundle-Composition
```

**Impact:** Kleinere Bundles, schnelleres Laden

---

### **2.4 Security-Hardening**

#### **2.4.1 Input-Validation (Frontend)**
**Tasks:**
- [ ] Zod-Schemas für alle Forms
- [ ] Sanitization für User-Input
- [ ] XSS-Prevention
- [ ] CSRF-Token-Support

**Code:**
```typescript
import { z } from 'zod';

const emailSchema = z.object({
  subject: z.string().min(1).max(200),
  body: z.string().min(1).max(10000),
  to: z.string().email(),
});

// Validate
const result = emailSchema.safeParse(formData);
if (!result.success) {
  // Show errors
}
```

**Impact:** XSS-geschützt

---

#### **2.4.2 Rate-Limiting (Backend)**
**Tasks:**
- [ ] slowapi installieren
- [ ] Rate-Limiter für alle Endpoints
- [ ] IP-basiertes Limiting
- [ ] API-Key-Support

**Code:**
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/agent/start")
@limiter.limit("5/minute")
async def start_agent():
    # Max 5 Requests pro Minute
    pass
```

**Impact:** DoS-geschützt

---

#### **2.4.3 Security-Headers**
**Tasks:**
- [ ] Helmet.js-äquivalent für FastAPI
- [ ] CSP-Header
- [ ] X-Frame-Options
- [ ] HSTS

**Code:**
```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "*.ihre-domain.de"])

@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000"
    return response
```

**Impact:** Production-ready Security

---

## 📊 PHASE 2 METRICS

### **Success-Kriterien:**

| Metrik | Ziel | Messung |
|--------|------|---------|
| **Bundle-Size** | < 500 KB | Vite Build Output |
| **API Response** | < 200ms | Network Tab |
| **Error-Rate** | < 0.1% | Error-Tracking |
| **Offline-Support** | 100% | PWA-Audit |
| **Security-Score** | A+ | Security-Headers.com |
| **Type-Coverage** | 100% | TypeScript |

---

## 🗓️ TIMELINE

```
Tag 1-2: Contexts Migration
├── EmailContext → Backend (4h)
├── AgentContext → Backend (3h)
├── PracticeContext → Backend (2h)
└── Testing (3h)

Tag 3: Offline-First
├── Service Worker (2h)
├── IndexedDB Setup (2h)
├── Sync-Queue (3h)
└── Testing (1h)

Tag 4: Performance
├── Code-Splitting (2h)
├── Bundle-Optimierung (2h)
├── Image-Optimierung (1h)
└── Testing (1h)

Tag 5: Security
├── Input-Validation (2h)
├── Rate-Limiting (1h)
├── Security-Headers (1h)
└── Security-Audit (2h)
```

**Total: 5 Tage (40 Stunden)**

---

## 🎯 DELIVERABLES

**Am Ende von Phase 2:**
- ✅ Vollständig Backend-integrierte Contexts
- ✅ PWA mit Offline-Support
- ✅ < 500 KB Bundle-Size
- ✅ A+ Security-Score
- ✅ < 200ms API Response-Time
- ✅ 100% TypeScript-Coverage
- ✅ Production-Ready

---

## 🚀 QUICK-WINS (Sofort umsetzbar)

### **1. Lazy-Loading (30 Min)**
```typescript
// Sofort -60% Initial Bundle
const Dashboard = lazy(() => import('./pages/Dashboard'));
```

### **2. React Query Devtools (10 Min)**
```bash
npm install @tanstack/react-query-devtools
```

### **3. Vite Bundle-Analyzer (10 Min)**
```bash
npm install --save-dev rollup-plugin-visualizer
```

---

## 📝 RISIKO-MANAGEMENT

### **Hohe Risiken:**
- Contexts-Migration könnte Breaking Changes verursachen
  - **Mitigation:** Feature-Flags, schrittweise Migration

### **Mittlere Risiken:**
- Service Worker könnte Caching-Probleme verursachen
  - **Mitigation:** Versionierung, Cache-Invalidation

### **Niedrige Risiken:**
- Bundle-Optimierung könnte Build-Zeit erhöhen
  - **Mitigation:** Acceptable Trade-off

---

## 🎯 PHASE 2 START-CHECKLISTE

Vor Start von Phase 2:
- [ ] Phase 1 komplett getestet
- [ ] Keine kritischen Bugs in Phase 1
- [ ] Backup des aktuellen Stands
- [ ] Dependencies aktualisiert
- [ ] Team-Alignment

---

**Erstellt von:** Senior System-Architect  
**Review:** CEO-Level  
**Approved:** ✅ Ready for Phase 2  
**Next:** Warten auf Go-Ahead

