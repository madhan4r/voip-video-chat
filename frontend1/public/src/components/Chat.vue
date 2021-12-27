<template>
  <div>
    <div id="chat">
      <h1>
        Welcome to the Vue chat app<span v-if="nameRegistered"
          >, {{ name }}</span
        >!
      </h1>
      <p>{{ statusString }}</p>
      <div v-if="!nameRegistered">
        <input
          @keyup.enter="registerName"
          v-model="name"
          placeholder="Enter your name"
        />
        <button @click="registerName">Register name</button>
      </div>
      <div v-if="nameRegistered && !activeConversation && isConnected">
        <input v-model="room_name" placeholder="Enter room name" />
        <button v-if="room_name" @click="createOrJoinGeneralChannel">
          Join chat
        </button>
      </div>
      <Conversation
        v-if="activeConversation"
        :active-conversation="activeConversation"
        :name="name"
      />
    </div>
  </div>
</template>
<script>
import { Client } from "twilio-chat";
import axios from "axios";
import Conversation from "./Conversation";

export default {
  name: "Chat",
  components: { Conversation },
  data: () => ({
    token: null,
    statusString: "",
    name: "",
    nameRegistered: false,
    isConnected: false,
    activeConversation: "",
    room_name: "",
  }),
  methods: {
    async getToken() {
      return axios
        .post(
          `http://localhost/api/v1/communication/token?identity=${this.name}`
        )
        .then((res) => {
          this.token = res.data;
          return res;
        });
    },
    async initConversationsClient() {
      this.conversationsClient = new Client(this.token.token, {
        logLevel: "info",
      });
      this.statusString = "Connecting to Twilio...";
      this.conversationsClient.on("connectionStateChanged", (state) => {
        switch (state) {
          case "connected":
            this.statusString = "You are connected.";
            this.isConnected = true;
            break;
          case "disconnecting":
            this.statusString = "Disconnecting from Twilio...";
            break;
          case "disconnected":
            this.statusString = "Disconnected.";
            break;
          case "denied":
            this.statusString = "Failed to connect.";
            break;
        }
      });
      // when the access token is about to expire, refresh it
      this.conversationsClient.on("tokenAboutToExpire", () => {
        this.refreshToken();
      });

      // if the access token already expired, refresh it
      this.conversationsClient.on("tokenExpired", () => {
        this.refreshToken();
      });
    },
    registerName: async function () {
      this.nameRegistered = true;
      await this.getToken();
      this.initConversationsClient();
    },
    async createOrJoinGeneralChannel() {
      // Get the general chat channel, which is where all the messages are
      // sent in this simple application
      this.print("Attempting to join chat...");
      this.conversationsClient
        .getChannelByUniqueName("general")
        .then((channel) => {
          this.activeConversation = channel;
          console.log("Found general channel:");
          console.log(this.activeConversation);
          this.setupChannel();
        })
        .catch(() => {
          // If it doesn't exist, let's create it
          console.log("Creating general channel");
          this.conversationsClient
            .createChannel({
              uniqueName: "general",
              friendlyName: this.room_name,
            })
            .then((channel) => {
              console.log("Created general channel:");
              console.log(channel);
              this.activeConversation = channel;
              this.setupChannel();
            })
            .catch((channel) => {
              console.log("Channel could not be created:");
              console.log(channel);
            });
        });
    },
    // Set up channel after it has been found
    setupChannel() {
      // Join the general channel
      this.activeConversation.join().then((channel) => {
        this.print(`Joined channel as ${this.name}`);
      });
    },
    print(infoMessage) {
      this.statusString = infoMessage;
    },
    async refreshToken() {
      console.log("Token about to expire");
      // Make a secure request to your backend to retrieve a refreshed access token.
      // Use an authentication mechanism to prevent token exposure to 3rd parties.
      await this.getToken();
      console.log("updated token for chat client");
      this.conversationsClient.updateToken(this.token.token);
    },
  },
};
</script>
<style scoped></style>
