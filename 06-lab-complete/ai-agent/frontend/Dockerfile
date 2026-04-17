# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files (local to frontend context)
COPY package.json package-lock.json* ./
RUN npm install --no-audit --no-fund

# Build arguments for Vite (baked at build time)
ARG VITE_API_BASE_URL
ARG VITE_AGENT_API_KEY
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_AGENT_API_KEY=$VITE_AGENT_API_KEY

# Copy all source files
COPY . ./
RUN npm run build

# Stage 2: Serve
FROM nginx:alpine

# Copy build files from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy Nginx proxy template (envvars will be substituted at startup)
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
