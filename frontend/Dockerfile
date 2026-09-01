FROM node:20-alpine

WORKDIR /app

# Install dependencies with lockfile guarantee
COPY package.json package-lock.json ./
RUN npm ci

# Copy frontend source code
COPY . .

# Set environment variables for Next.js production build
ENV NODE_ENV=production \
    PORT=3000 \
    HOSTNAME="0.0.0.0"

RUN npm run build

EXPOSE 3000

# Health check to ensure Next.js server is serving requests
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/ || exit 1

CMD ["npm", "run", "start"]
