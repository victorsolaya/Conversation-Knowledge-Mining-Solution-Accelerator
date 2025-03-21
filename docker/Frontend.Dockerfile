# Stage 1: Build frontend
FROM node:20-alpine AS frontend  
RUN mkdir -p /home/node/app/node_modules && chown -R node:node /home/node/app

WORKDIR /home/node/app 

# Install dependencies
COPY ./src/frontend/package*.json ./  
USER node
RUN npm ci  

# Copy source code and build
COPY --chown=node:node ./src/frontend/ ./frontend  
WORKDIR /home/node/app/frontend
RUN npm run build

# Set expose port 
EXPOSE 3000

CMD ["npm", "start"]