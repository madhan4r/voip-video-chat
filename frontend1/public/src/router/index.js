import Vue from "vue";
import VueRouter from "vue-router";
import Home from "../views/Home.vue";
import Voice from "@/components/Voice.vue"
import Video from "@/components/VideoHome.vue"
import Chat from "@/components/Chat.vue"

Vue.use(VueRouter);

const routes = [
  {
    path: "/",
    name: "Home",
    component: Home,
  },
  {
    path: "/voice",
    name: "Voice",
    component: Voice,
  },
  {
    path: "/video",
    name: "Video",
    component: Video,
  },
  {
    path: "/chat",
    name: "Chat",
    component: Chat,
  },
  {
    path: "/about",
    name: "About",
    // route level code-splitting
    // this generates a separate chunk (about.[hash].js) for this route
    // which is lazy-loaded when the route is visited.
    component: () =>
      import(/* webpackChunkName: "about" */ "../views/About.vue"),
  },
];

const router = new VueRouter({
  mode: "history",
  base: process.env.BASE_URL,
  routes,
});

export default router;
