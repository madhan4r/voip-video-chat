# Stage 0, "build-stage", based on Node.js, to build and compile the frontend
FROM node:14-buster-slim as build-stage

WORKDIR /app

COPY package*.json /app/

# #RUN apk add --no-cache git

RUN if test -e package-lock.json; then echo "Package Lock file Exists" && rm package-lock.json; fi
RUN if test -d node_modules; then echo "Node Modules Exists" && rm -rf node_modules; fi

RUN npm install

COPY ./ /app/

ARG FRONTEND_ENV=production

ENV VUE_APP_ENV=${FRONTEND_ENV}

# Comment out the next line to disable tests
# RUN npm run test:unit

RUN npm run build --mode ${FRONTEND_ENV}


# Stage 1, based on Nginx, to have only the compiled app, ready for production with Nginx
FROM nginx:1.15

COPY --from=build-stage /app/dist/ /usr/share/nginx/html

RUN rm -v /etc/nginx/conf.d/default.conf

COPY ./nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
