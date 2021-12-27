<template>
  <div class="home">
    <button @click="navigateTo('/voice')">Voice</button>
    <button @click="navigateTo('/video')">Video</button>
    <button @click="navigateTo('/chat')">Chat</button>
  </div>
</template>

<script>
export default {
  name: "Home",
  methods: {
    navigateTo(path) {
      this.$router.push(path);
    },
  },
};
</script>
