/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8000/api/:path*", // Proxy API calls
      },
      {
        source: "/rtc",
        destination: "http://localhost:8000/rtc",
      },
    ];
  },
};

export default nextConfig;
