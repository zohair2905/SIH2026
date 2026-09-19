import type { NextConfig } from "next";

const backendUrl = process.env.BACKEND_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  turbopack: {
    root: __dirname,
  },
  rewrites: async () => ({
    // Fallback runs after route handlers and dynamic routes, so the
    // dedicated /api/auth/* and /api/audit-logs handlers (cookie shaping,
    // status forwarding) keep precedence. Every other /api/* call — cases,
    // alerts, dashboard, heatmap, transactions, predictions — is proxied to
    // FastAPI with the browser's `sih_access_token` cookie preserved, which
    // the backend authenticates directly.
    fallback: [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/api/:path*`,
      },
    ],
  }),
};

export default nextConfig;
