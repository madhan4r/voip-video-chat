<template>
  <div class="home mt-5 text-center">
    <CButton
      class="btn-primary"
      style="margin-right: 10px"
      @click="navigateTo('/voice')"
      >Voice
    </CButton>
    <CButton
      class="btn-secondary"
      style="margin-right: 10px"
      @click="navigateTo('/video')"
      >Video
    </CButton>
    <CButton class="btn-success" @click="navigateTo('/chat')">Chat</CButton>
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
