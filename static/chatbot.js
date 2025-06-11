// ===================== CHATBOT LOGIC =====================
function sendMessage() {
  var userInput = document.getElementById("userInput");
  var message = userInput.value;
  if (message.trim() === "") {
    return;
  }
  displayMessage(message, "user-message");
  userInput.value = "";
  showLoading();
  fetch(`/get?msg=${encodeURIComponent(message)}`)
    .then((response) => response.text())
    .then((data) => {
      removeLoading();
      displayBotMarkdown(data);
    })
    .catch(() => {
      removeLoading();
      displayBotMarkdown(
        "Erreur lors de la récupération de la réponse du chatbot."
      );
    });
}

function displayMessage(message, className) {
  var chatbox = document.getElementById("chatbox");
  var messageDiv = document.createElement("div");
  messageDiv.classList.add("message", className);
  var icon = document.createElement("span");
  icon.classList.add("icon");
  if (className === "user-message") {
    icon.innerHTML = '<i class="fa-solid fa-user"></i>';
  } else {
    icon.innerHTML = '<i class="fa-solid fa-robot"></i>';
  }
  messageDiv.appendChild(icon);
  var textSpan = document.createElement("span");
  textSpan.textContent = message;
  messageDiv.appendChild(textSpan);
  chatbox.appendChild(messageDiv);
  chatbox.scrollTop = chatbox.scrollHeight;
}

function displayBotMarkdown(markdownText) {
  var chatbox = document.getElementById("chatbox");
  var messageDiv = document.createElement("div");
  messageDiv.classList.add("message", "bot-message");
  var icon = document.createElement("span");
  icon.classList.add("icon");
  icon.innerHTML = '<i class="fa-solid fa-robot"></i>';
  messageDiv.appendChild(icon);
  var textSpan = document.createElement("span");
  textSpan.innerHTML = window.marked.parse(markdownText);
  messageDiv.appendChild(textSpan);
  // Nouveau bouton TTS stylé
  var ttsBtn = document.createElement("button");
  ttsBtn.className = "tts-btn";
  ttsBtn.title = "Lire la réponse (voix GLaDOS)";
  ttsBtn.innerHTML = '<i class="fa-solid fa-volume-high"></i>';
  ttsBtn.onclick = function () {
    ttsBtn.classList.add("playing");
    speakText(stripMarkdown(markdownText), function () {
      ttsBtn.classList.remove("playing");
    });
  };
  messageDiv.appendChild(ttsBtn);
  chatbox.appendChild(messageDiv);
  chatbox.scrollTop = chatbox.scrollHeight;
}

// Fonction pour lire le texte (TTS) avec voix française prioritaire
function speakText(text, onend) {
  if (!window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  var utter = new SpeechSynthesisUtterance(text);
  // Recherche d'une voix française prioritaire
  var voices = window.speechSynthesis.getVoices();
  var frVoice = voices.find(
    (v) => v.lang && v.lang.toLowerCase().startsWith("fr")
  );
  if (frVoice) {
    utter.voice = frVoice;
    utter.lang = frVoice.lang;
  } else {
    utter.lang = "fr-FR";
  }
  utter.rate = 1;
  utter.pitch = 1;
  utter.volume = 1;
  utter.onend = function () {
    if (onend) onend();
  };
  window.speechSynthesis.speak(utter);
}

function stripMarkdown(md) {
  var tmp = document.createElement("div");
  tmp.innerHTML = window.marked.parse(md);
  return tmp.textContent || tmp.innerText || "";
}

function showLoading() {
  var chatbox = document.getElementById("chatbox");
  var loadingDiv = document.createElement("div");
  loadingDiv.classList.add("message", "bot-message");
  loadingDiv.id = "loading-message";
  loadingDiv.innerHTML =
    '<span class="icon"><i class="fa-solid fa-robot"></i></span><span><i class="fa-solid fa-spinner fa-spin"></i> Le chatbot réfléchit...</span>';
  chatbox.appendChild(loadingDiv);
  chatbox.scrollTop = chatbox.scrollHeight;
}

function removeLoading() {
  var loadingDiv = document.getElementById("loading-message");
  if (loadingDiv) loadingDiv.remove();
}

// ===================== PDF MANAGEMENT =====================
function refreshPdfList() {
  fetch("/list_pdfs")
    .then((res) => res.json())
    .then((data) => {
      var pdfList = document.getElementById("pdfList");
      pdfList.innerHTML = "";
      if (data.pdfs && data.pdfs.length > 0) {
        data.pdfs.forEach((pdf) => {
          var item = document.createElement("div");
          item.className = "pdf-item";
          var name = document.createElement("span");
          name.className = "pdf-name";
          name.innerHTML =
            '<i class="fa-solid fa-file-pdf" style="color:#e53935"></i> ' + pdf;
          var del = document.createElement("button");
          del.className = "delete-btn";
          del.innerHTML = '<i class="fa-solid fa-trash"></i>';
          del.onclick = function () {
            deletePdf(pdf);
          };
          item.appendChild(name);
          item.appendChild(del);
          pdfList.appendChild(item);
        });
      } else {
        pdfList.innerHTML = '<span style="color:#888">Aucun PDF ingéré.</span>';
      }
    });
}

function deletePdf(pdf) {
  fetch("/delete_pdf", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ filename: pdf }),
  }).then(() => refreshPdfList());
}

document
  .getElementById("userInput")
  .addEventListener("keyup", function (event) {
    event.preventDefault();
    if (event.key === "Enter") {
      document.querySelector(".send-btn").click();
    }
  });

document.getElementById("uploadForm").addEventListener("submit", function (e) {
  e.preventDefault();
  var formData = new FormData();
  var files = document.getElementById("fileInput").files;
  if (files.length === 0) {
    document.getElementById("uploadStatus").textContent =
      "Veuillez sélectionner un ou plusieurs fichiers.";
    document.getElementById("uploadStatus").style.color = "#e53935";
    return;
  }
  for (var i = 0; i < files.length; i++) {
    formData.append("file", files[i]);
  }
  document.getElementById("uploadStatus").textContent = "Envoi en cours...";
  document.getElementById("uploadStatus").style.color = "#2193b0";
  fetch("/upload", {
    method: "POST",
    body: formData,
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        document.getElementById("uploadStatus").textContent =
          "Fichier(s) ingéré(s) avec succès !";
        document.getElementById("uploadStatus").style.color = "#388e3c";
        refreshPdfList();
      } else {
        document.getElementById("uploadStatus").textContent =
          "Erreur lors de l'ingestion.";
        document.getElementById("uploadStatus").style.color = "#e53935";
      }
    })
    .catch(() => {
      document.getElementById("uploadStatus").textContent =
        "Erreur lors de l'envoi.";
      document.getElementById("uploadStatus").style.color = "#e53935";
    });
});
// ===================== INIT =====================
refreshPdfList();
