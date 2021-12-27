# base image
FROM node:14-buster-slim

RUN mkdir -p /frontend/public /frontend/src
COPY ./public /frontend/public
COPY ./src /frontend/src
COPY ./*js /frontend/
COPY ./*.env* /frontend/
COPY ./package.json /frontend/package.json
COPY ./vue.config.js /frontend/vue.config.js

# set working directory
WORKDIR /frontend
RUN pwd
RUN ls

RUN npm install
ENV PORT=80
EXPOSE 80       
CMD ["npm", "run", "serve"]
