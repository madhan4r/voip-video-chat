<template>
  <div>
    <div style="text-align: left">
      <input type="text" placeholder="client name" v-model="client_name" />
      <button @click="getToken()">get token</button>
    </div>
    <div id="controls">
      <div id="info">
        <p class="instructions">Twilio Client</p>
        <div id="client-name"></div>
        <div id="output-selection">
          <label>Ringtone Devices</label>
          <select id="ringtone-devices" multiple></select>
          <label>Speaker Devices</label>
          <select id="speaker-devices" multiple></select
          ><br />
        </div>
      </div>
      <div id="call-controls">
        <p class="instructions">Make a Call:</p>
        <input
          id="phone-number"
          type="text"
          placeholder="Enter a phone # or client name"
        />
        <button id="button-call" @click="makeCall()">Call</button>
        <button id="button-hangup" @click="hangUp()">Hangup</button>
        <div id="volume-indicators">
          <label>Mic Volume</label>
          <div id="input-volume"></div>
          <br /><br />
          <label>Speaker Volume</label>
          <div id="output-volume"></div>
        </div>
      </div>
      <div id="log"></div>
    </div>
  </div>
</template>
<script>
import { Device } from "@twilio/voice-sdk";
import axios from "axios";
export default {
  name: "Voice",
  data: () => ({
    client_name: "",
    token: null,
    device: null,
  }),
  created() {
    // When a user is about to transition away from this page,
    // disconnect from the call.
    window.addEventListener("beforeunload", this.hangUp);          
  },
  methods: {
    async getToken() {
      this.log("Requesting Access Token...");
      axios
        .post(
          `http://localhost/api/v1/communication/token?identity=${this.client_name}`
        )
        .then((res) => {
          this.log("Access Token Recieved...");
          this.token = res.data;
          this.device = new Device(this.token.token, {
            closeProtection: true,
            // Set Opus as our preferred codec. Opus generally performs better, requiring less bandwidth and
            // providing better audio quality in restrained network conditions. Opus will be default in 2.0.
            codecPreferences: ["opus", "pcmu"],
            // Use fake DTMF tones client-side. Real tones are still sent to the other end of the call,
            // but the client-side DTMF tones are fake. This prevents the local mic capturing the DTMF tone
            // a second time and sending the tone twice. This will be default in 2.0.
            fakeLocalDTMF: true,
            // Use `enableRingingState` to enable the device to emit the `ringing`
            // state. The TwiML backend also needs to have the attribute
            // `answerOnBridge` also set to true in the `Dial` verb. This option
            // changes the behavior of the SDK to consider a call `ringing` starting
            // from the connection to the TwiML backend to when the recipient of
            // the `Dial` verb answers.
            enableRingingState: true,
            logLevel: "error",
          });
          this.deviceReady();
        });
    },
    async deviceReady() {
      this.device.register();
      this.device.on("registered", () => {
        this.log("Twilio.Device Ready!");
        document.getElementById("call-controls").style.display = "block";
      });
      this.device.on("error", (error) => {
        this.log("Twilio.Device Error: " + error.message);
      });
      this.device.on("incoming", (conn) => {
        this.log("Incoming connection from " + conn.parameters.From);
        var archEnemyPhoneNumber = "+12093373517";
        if (conn.parameters.From === archEnemyPhoneNumber) {
          conn.reject();
          this.log("It's your nemesis. Rejected call.");
        } else {
          // accept the incoming connection and start two-way audio
          conn.accept();
        }
      });
      this.setClientNameUI(this.token.identity);
      this.device.audio.on(
        "deviceChange",
        this.updateAllDevices.bind(this.device)
      );
      // Show audio selection UI if it is supported by the browser.
      if (this.device.audio.isOutputSelectionSupported) {
        document.getElementById("output-selection").style.display = "block";
      }
    },
    async makeCall() {
      // get the phone number to connect the call to
      var params = {
        phone: document.getElementById("phone-number").value,
      };
      this.log("Calling " + params.phone + "...");
      if (this.device) {
        var outgoingConnection = await this.device.connect({ params });
        outgoingConnection.on("initiated", () => {
          this.log("Initiated...");
        });
        outgoingConnection.on("ringing", () => {
          this.log("Ringing...");
        });
        outgoingConnection.on("accept", () => {
          this.log("Successfully established call!");
          document.getElementById("button-call").style.display = "none";
          document.getElementById("button-hangup").style.display = "inline";
          document.getElementById("volume-indicators").style.display = "block";
          this.bindVolumeIndicators(outgoingConnection);
        });
        outgoingConnection.on("answered", () => {
          this.log("Answered!");
        });
        outgoingConnection.on("completed", () => {
          this.log("Call Completed!");
        });
        outgoingConnection.on("reject", () => {
          this.log("Call rejected!");
        });
        outgoingConnection.on("error", (err) => {
          this.log(err);
        });
        outgoingConnection.on("disconnect", () => {
          this.log("Call ended.");
          document.getElementById("button-call").style.display = "inline";
          document.getElementById("button-hangup").style.display = "none";
          document.getElementById("volume-indicators").style.display = "none";
        });
      }
    },
    hangUp() {
      this.log("Hanging up...");
      if (this.device) {
        this.device.disconnectAll();
      }
    },
    getDevices() {
      navigator.mediaDevices
        .getUserMedia({ audio: true })
        .then(this.updateAllDevices.bind(this.device));
    },
    updateAllDevices() {
      var speakerDevices = document.getElementById("speaker-devices");
      var ringtoneDevices = document.getElementById("ringtone-devices");
      this.updateDevices(
        speakerDevices,
        this.device.audio.speakerDevices.get()
      );
      this.updateDevices(
        ringtoneDevices,
        this.device.audio.ringtoneDevices.get()
      );
    },
    // Update the available ringtone and speaker devices
    updateDevices(selectEl, selectedDevices) {
      selectEl.innerHTML = "";

      this.device.audio.availableOutputDevices.forEach(function (device, id) {
        var isActive = selectedDevices.size === 0 && id === "default";
        selectedDevices.forEach(function (device) {
          if (device.deviceId === id) {
            isActive = true;
          }
        });
        var option = document.createElement("option");
        option.label = device.label;
        option.setAttribute("data-id", id);
        if (isActive) {
          option.setAttribute("selected", "selected");
        }
        selectEl.appendChild(option);
      });
    },
    log(message) {
      var logDiv = document.getElementById("log");
      logDiv.innerHTML += "<p>&gt;&nbsp;" + message + "</p>";
      logDiv.scrollTop = logDiv.scrollHeight;
    },
    setClientNameUI(clientName) {
      var div = document.getElementById("client-name");
      div.innerHTML = "Your client name: <strong>" + clientName + "</strong>";
    },
    bindVolumeIndicators(connection) {
      var outputVolumeBar = document.getElementById("output-volume");
      var inputVolumeBar = document.getElementById("input-volume");
      connection.on("volume", function (inputVolume, outputVolume) {
        var inputColor = "red";
        if (inputVolume < 0.5) {
          inputColor = "green";
        } else if (inputVolume < 0.75) {
          inputColor = "yellow";
        }

        inputVolumeBar.style.width = Math.floor(inputVolume * 300) + "px";
        inputVolumeBar.style.background = inputColor;

        var outputColor = "red";
        if (outputVolume < 0.5) {
          outputColor = "green";
        } else if (outputVolume < 0.75) {
          outputColor = "yellow";
        }

        outputVolumeBar.style.width = Math.floor(outputVolume * 300) + "px";
        outputVolumeBar.style.background = outputColor;
      });
    },
  },
};
</script>
<style scoped>
label {
  text-align: left;
  font-family: Helvetica, sans-serif;
  font-size: 1.25em;
  color: #777776;
  display: block;
}

div#controls {
  padding: 3em;
  max-width: 1200px;
  margin: 0 auto;
}

div#controls div {
  float: left;
}

div#controls div#call-controls,
div#controls div#info {
  width: 16em;
  margin: 0 1.5em;
  text-align: center;
}
div#controls div#info div#output-selection {
  display: none;
}

div#controls div#info a {
  font-size: 1.1em;
  color: khaki;
  text-decoration: underline;
  cursor: pointer;
}

div#controls div#info select {
  width: 300px;
  height: 60px;
  margin-bottom: 2em;
}

div#controls div#info label {
  width: 300px;
}

div#controls div#call-controls div#volume-indicators {
  display: none;
  padding: 10px;
  margin-top: 20px;
  width: 500px;
  text-align: left;
}

div#controls div#call-controls div#volume-indicators > div {
  display: block;
  height: 20px;
  width: 0;
}

div#controls p.instructions {
  text-align: left;
  margin-bottom: 1em;
  font-family: Helvetica-LightOblique, Helvetica, sans-serif;
  font-style: oblique;
  font-size: 1.25em;
  color: #777776;
}

div#controls div#info #client-name {
  text-align: left;
  margin-bottom: 1em;
  font-family: "Helvetica Light", Helvetica, sans-serif;
  font-size: 1.25em;
  color: #777776;
}

div#controls button {
  width: 15em;
  height: 2.5em;
  margin-top: 1.75em;
  border-radius: 1em;
  font-family: "Helvetica Light", Helvetica, sans-serif;
  font-size: 0.8em;
  font-weight: lighter;
  outline: 0;
}

div#controls button:active {
  position: relative;
  top: 1px;
}

div#controls div#call-controls {
  display: none;
}

div#controls div#call-controls input {
  font-family: Helvetica-LightOblique, Helvetica, sans-serif;
  font-style: oblique;
  font-size: 1em;
  width: 100%;
  height: 2.5em;
  padding: 0.5em;
  display: block;
}

div#controls div#call-controls button {
  /* color: #fff; */
  background: 0 0;
  border: 1px solid #686865;
}

div#controls div#call-controls button#button-hangup {
  display: none;
}

div#controls div#log {
  border: 1px solid #686865;
  width: 35%;
  height: 9.5em;
  margin-top: 2.75em;
  text-align: left;
  padding: 1.5em;
  float: right;
  overflow-y: scroll;
}

div#controls div#log p {
  color: #686865;
  font-family: "Share Tech Mono", "Courier New", Courier, fixed-width;
  font-size: 1.25em;
  line-height: 1.25em;
  margin-left: 1em;
  text-indent: -1.25em;
  width: 90%;
}
</style>
