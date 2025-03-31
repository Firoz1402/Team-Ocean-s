const splash = document.querySelector(".splash");
const main_display = document.querySelector(".main-content");
const cta_button = document.querySelector(".cta-button");

const messageInput = document.querySelector(".message-text");
const sendButton = document.querySelector(".send-button");
const messageContainer = document.querySelector(".message-container");
const title = document.querySelector(".chat-body-header");

if (main_display) main_display.style.display = "none";

setTimeout(() => {
  if (splash) {
    splash.classList.add("fade-out");
    setTimeout(() => {
      splash.style.display = "none";
      main_display.classList.add("fade-in");
      main_display.style.display = "flex";
      main_display.style.flexDirection = "column";
    }, 1000);
  }
}, 2000);

function changeThePage() {
  window.location.href = "chat.html";
}

function adjustHeight(element) {
  element.style.height = "35px";
  if (element.scrollHeight <= 150) {
    element.style.height = element.scrollHeight + "px";
  } else {
    element.style.height = "150px";
  }
}
if (sendButton)
  sendButton.addEventListener("click", async (e) => {
    e.preventDefault();
    const message = messageInput.value.trim();
    if (message === "") {
      return;
    }
    if (message) {
      if (title) {
        title.style.display = "none";
        if (messageContainer) messageContainer.style.display = "block";
      }

      const messageElement = document.createElement("div");
      messageElement.classList.add("client-message");

      const messageText = document.createElement("p");
      messageText.innerText = message;
      messageElement.appendChild(messageText);
      messageContainer.appendChild(messageElement);
      messageInput.value = "";

      const response = await fetch(
        `http://localhost:5000/generate-clean-speech?text=${message}`
      );
      const data = await response.json();
      console.log(data);

      const divElement = document.createElement("div");
      divElement.classList.add("server-message");
      divElement.style.flexDirection = "column";
      divElement.style.marginBottom = "20px";

      const table = document.createElement("table");

      const headers = ["Name", "Percentage", "Score"];
      const thead = document.createElement("thead");
      const headerRow = document.createElement("tr");

      headers.forEach((headerText) => {
        const th = document.createElement("th");
        th.innerText = headerText;
        headerRow.appendChild(th);
      });

      thead.appendChild(headerRow);
      table.appendChild(thead);

      const tbody = document.createElement("tbody");

      const serverTitleOne = document.createElement("span");
      serverTitleOne.innerText = "Overall Toxicity Score: ";
      serverTitleOne.style.fontWeight = "bold";
      serverTitleOne.style.fontSize = "18px";
      serverTitleOne.style.color = "#f12df1";

      const serverMessage = document.createElement("p");
      serverMessage.style.display = "inline";
      serverMessage.appendChild(serverTitleOne);

      const textNode = document.createTextNode(
        `${data.analysis.overall_toxicity}`
      );
      serverMessage.appendChild(textNode);

      divElement.appendChild(serverMessage);

      const values = data.analysis.category_breakdown;
      values.forEach((value) => {
        console.log(value);
        const row = document.createElement("tr");

        const td1 = document.createElement("td");
        td1.innerText = value.name;

        const td2 = document.createElement("td");
        td2.innerText = `${value.percentage}%`;

        const td3 = document.createElement("td");
        td3.innerText = value.score;

        row.appendChild(td1);
        row.appendChild(td2);
        row.appendChild(td3);
        tbody.appendChild(row);
      });

      table.appendChild(tbody);
      divElement.appendChild(table);

      const cleanedSpeechContainer = document.createElement("p");
      cleanedSpeechContainer.style.display = "inline";

      const cleanedSpeechTitle = document.createElement("span");
      cleanedSpeechTitle.innerText = "Cleaned Speech: ";
      cleanedSpeechTitle.style.fontWeight = "bold";
      cleanedSpeechTitle.style.fontSize = "18px";
      cleanedSpeechTitle.style.color = "#f12df1";

      const cleanedSpeechText = document.createElement("span");
      cleanedSpeechText.innerText = data.cleaned_speech;

      cleanedSpeechContainer.appendChild(cleanedSpeechTitle);
      cleanedSpeechContainer.appendChild(cleanedSpeechText);
      divElement.appendChild(cleanedSpeechContainer);

      messageContainer.appendChild(divElement);

      const secondData = data.reasons
        .map((reason) => {
          return reason;
        })
        .join(", ");
      console.log(secondData);
      const secondDivElement = document.createElement("div");
      secondDivElement.classList.add("server-message");
      secondDivElement.style.flexDirection = "column";

      const toxicTitle = document.createElement("span");
      toxicTitle.innerText = "Toxic Words: ";
      toxicTitle.style.fontWeight = "bold";
      toxicTitle.style.color = "#ff6666";

      const toxicMessage = document.createElement("span");
      toxicMessage.style.display = "inline";
      toxicMessage.appendChild(toxicTitle);

      const toxicWords = data.toxic_words.map((word) => word.trim()); 
      const wordsPerLine = 5;

      const toxicMessagetwo = document.createElement("span");

      // Break words into chunks of `wordsPerLine`
      for (let i = 0; i < toxicWords.length; i += wordsPerLine) {
        const chunk = toxicWords.slice(i, i + wordsPerLine).join(", "); 
        toxicMessagetwo.append(chunk);
        toxicMessagetwo.appendChild(document.createElement("br"));
      }

      // Append to container
      const toxicContainer = document.getElementById("toxic-container");
      if (toxicContainer) {
        secondDivElement.appendChild(toxicMessage);

        toxicContainer.appendChild(toxicMessagetwo);
      } else {
        console.error("Element with id 'toxic-container' not found!");
      }

      if (typeof secondDivElement !== "undefined" && secondDivElement) {
        secondDivElement.appendChild(toxicMessage);
        secondDivElement.appendChild(toxicMessagetwo);
      }

      messageContainer.appendChild(secondDivElement);

      const reasonTitle = document.createElement("span");
      reasonTitle.innerText = "Reasons: ";
      reasonTitle.style.fontWeight = "bold";
      reasonTitle.style.color = "#ff69b4";

      const secondMessage = document.createElement("p");
      secondMessage.style.display = "inline";
      secondMessage.appendChild(reasonTitle);
      const reasonText = document.createTextNode(`${secondData}`);
      secondMessage.appendChild(reasonText);

      secondDivElement.appendChild(secondMessage);
      messageContainer.appendChild(secondDivElement);
      messageContainer.scrollTop = messageContainer.scrollHeight;
      const progressBar = document.getElementById("toxicity-progress");
      const percentageLabel = document.getElementById("toxicity-percentage");

      if (progressBar && percentageLabel) {
        const toxicityScore = data.analysis.overall_toxicity;

        progressBar.value = toxicityScore;
        percentageLabel.innerText = `${toxicityScore}%`;

        const progressColor = getProgressColor(toxicityScore);

        progressBar.style.background = "#ddd";
        progressBar.style.borderRadius = "5px";

        progressBar.style.setProperty("--progress-bar-color", progressColor);
      }
    }
  });

function getProgressColor(percentage) {
  if (percentage >= 80) return "#FF5F33";
  if (percentage >= 60) return "#FF9233";
  if (percentage >= 40) return "#FFC233";
  if (percentage >= 20) return "#FFDD33";
  return "#FFF533";
}
