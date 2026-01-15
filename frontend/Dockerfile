# NeurOS 2.0 Frontend Dockerfile

FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Expose port
EXPOSE 5173

# Run development server
CMD ["npm", "run", "dev", "--", "--host"]
