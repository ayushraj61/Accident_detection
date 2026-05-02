FROM node:18-alpine

WORKDIR /app

# Install dependencies first for Docker caching
COPY package.json package-lock.json ./
RUN npm install

# Copy all source code
COPY . .

EXPOSE 5173

# Expose host to connect from out of container
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
