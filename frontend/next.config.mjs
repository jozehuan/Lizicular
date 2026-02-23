import createNextIntlPlugin from 'next-intl/plugin';
const withNextIntl = createNextIntlPlugin('./i18n.ts');

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  typescript: {
    ignoreBuildErrors: true,
  },
  env: {
    NEXT_PUBLIC_BACKEND_URL: process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000",
  },
  images: {
    unoptimized: true,
  },
  async rewrites() {
    return [
      {
        source: "/api/backend/:path*",
        destination: `${process.env.INTERNAL_BACKEND_URL || "http://localhost:8000"}/:path*`,
      },
      {
        source: "/api/:path*",
        destination: `${process.env.INTERNAL_BACKEND_URL || "http://localhost:8000"}/:path*`,
      },
    ]
  },
}
export default withNextIntl(nextConfig);
