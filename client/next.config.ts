import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  env: {
    // Ensure these are exposed to the browser
    SERVER_IP: process.env.SERVER_IP,
    API_URL: process.env.EXPRESS_URL,
	EXPRESS_PORT: process.env.EXPRESS_PORT,
	FROM: process.env.FROM
  }
};

export default nextConfig;
