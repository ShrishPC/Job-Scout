FROM node:20-alpine

WORKDIR /app

# Set environment variables for Next.js
ENV NODE_ENV=development \
    PORT=3000 \
    HOSTNAME="0.0.0.0"

# Install dependencies with lockfile guarantee
COPY package.json package-lock.json ./
RUN npm ci

# Copy frontend source code
COPY . .

EXPOSE 3000

# Health check to ensure Next.js dev server is serving requests
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/ || exit 1

CMD ["npm", "run", "dev"]
