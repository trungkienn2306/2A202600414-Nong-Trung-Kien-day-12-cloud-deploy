# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files (local to frontend context)
COPY package.json package-lock.json* ./
RUN npm install --no-audit --no-fund

# Copy all source files
COPY . ./
RUN npx vite build

# Stage 2: Serve
FROM nginx:alpine

# Copy build files from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
