// ===================== CHATBOT LOGIC =====================
function sendMessage() {
  var userInput = document.getElementById("userInput");
  var message = userInput.value;
  if (message.trim() === "" && !activeReplyContext) {
    return;
  }

  let finalMessage = message;
  if (activeReplyContext) {
    const quotedOriginal = activeReplyContext
      .split("\n")
      .map((line) => `> ${line}`)
      .join("\n");
    finalMessage = `${quotedOriginal}\n\n${message.trim()}`;
  }

  displayMessage(finalMessage, "user-message");
  userInput.value = "";
  clearReplyContext();
  showLoading();
  fetch(`/get?msg=${encodeURIComponent(finalMessage)}`)
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
  icon.classList.add("material-icons"); // Changed from classList.add("icon") and innerHTML
  if (className === "user-message") {
    icon.textContent = "person"; // Material Icon name
  } else {
    icon.textContent = "smart_toy"; // Material Icon name
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
  icon.classList.add("material-icons");
  icon.textContent = "smart_toy";
  messageDiv.appendChild(icon);
  var textSpan = document.createElement("span");
  textSpan.innerHTML = window.marked.parse(markdownText);
  messageDiv.appendChild(textSpan);

  var ttsBtn = document.createElement("button");
  ttsBtn.className = "tts-btn ripple-effect-container";
  ttsBtn.title = "Lire la réponse";

  var ttsIcon = document.createElement("span");
  ttsIcon.classList.add("material-icons");
  ttsIcon.textContent = "volume_up"; // Default icon
  ttsBtn.appendChild(ttsIcon);

  ttsBtn.onclick = function (event) {
    if (ttsBtn.classList.contains("playing")) {
      window.speechSynthesis.cancel(); // Stop speaking
      ttsBtn.classList.remove("playing");
      ttsIcon.textContent = "volume_up"; // Reset icon
    } else {
      ttsBtn.classList.add("playing");
      ttsIcon.textContent = "stop"; // Modernized icon for stopping TTS
      speakText(stripMarkdown(markdownText), function () {
        ttsBtn.classList.remove("playing");
        ttsIcon.textContent = "volume_up"; // Reset icon when finished
      });
    }
  };
  messageDiv.appendChild(ttsBtn);

  // Add Reply Button
  var replyBtn = document.createElement("button");
  replyBtn.className = "reply-btn-md ripple-effect-container";
  replyBtn.title = "Répondre à ce message";

  var replyIcon = document.createElement("span");
  replyIcon.classList.add("material-icons");
  replyIcon.textContent = "reply";
  replyBtn.appendChild(replyIcon);

  replyBtn.onclick = function () {
    showReplyUI(markdownText);
  };
  messageDiv.appendChild(replyBtn);

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
function fetchPdfs() { // Renamed from refreshPdfList to better reflect it fetches and then refreshes
  fetch("/list_pdfs")
    .then((res) => res.json())
    .then((data) => {
      var pdfList = document.getElementById("pdfList");
      pdfList.innerHTML = ""; // Clear existing list
      if (data.pdfs && data.pdfs.length > 0) {
        data.pdfs.forEach((pdf) => {
          var item = document.createElement("div");
          item.className = "pdf-item";
          
          var name = document.createElement("span");
          name.className = "pdf-name";
          name.innerHTML = '<span class="material-icons">picture_as_pdf</span> ' + pdf; // Using Material Icon
          
          var delBtn = document.createElement("button");
          delBtn.className = "delete-btn-md ripple-effect-container"; // Apply MD3 style and ripple
          delBtn.title = "Supprimer le fichier";
          
          var delIcon = document.createElement("span");
          delIcon.classList.add("material-icons");
          delIcon.textContent = "delete"; // Material Icon for delete
          delBtn.appendChild(delIcon);
          
          delBtn.onclick = function () {
            deletePdf(pdf);
          };
          
          item.appendChild(name);
          item.appendChild(delBtn);
          pdfList.appendChild(item);
        });
      } else {
        pdfList.innerHTML = '<div class="pdf-item-empty"><span class="material-icons">info</span> Aucun PDF ingéré.</div>';
      }
      // Re-apply ripple effect to newly added buttons if not using event delegation
      if (typeof applyRippleEffect === 'function') {
        applyRippleEffect(); 
      }
    })
    .catch(error => {
      console.error("Error fetching PDF list:", error);
      var pdfList = document.getElementById("pdfList");
      pdfList.innerHTML = '<div class="pdf-item-empty"><span class="material-icons">error</span> Erreur au chargement des PDFs.</div>';
    });
}

function deletePdf(pdf) {
  fetch("/delete_pdf", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ filename: pdf }),
  })
  .then(response => {
    if (!response.ok) {
      throw new Error('Network response was not ok');
    }
    return response.json(); 
  })
  .then(() => {
    fetchPdfs(); // Refresh the list after deletion
  })
  .catch(error => {
    console.error("Error deleting PDF:", error);
    // Optionally, display an error message to the user here
  });
}

document
  .getElementById("userInput")
  .addEventListener("keyup", function (event) {
    event.preventDefault();
    if (event.key === "Enter") {
      document.querySelector(".send-btn").click();
    }
  });

// ===================== RIPPLE EFFECT =====================
function applyRippleEffect() {
  const rippleContainers = document.querySelectorAll(".ripple-effect-container");

  rippleContainers.forEach((container) => {
    container.addEventListener("click", function (e) {
      const ripple = document.createElement("span");
      ripple.classList.add("ripple");

      // Remove any existing ripples
      const existingRipple = container.querySelector(".ripple");
      if (existingRipple) {
        existingRipple.remove();
      }

      container.appendChild(ripple);

      const rect = container.getBoundingClientRect();
      // Calculate click position relative to the button
      // Account for page scroll
      const clickX = e.clientX - rect.left;
      const clickY = e.clientY - rect.top;

      // Set ripple position and size
      const size = Math.max(rect.width, rect.height);
      ripple.style.width = ripple.style.height = size + "px";
      ripple.style.left = clickX - size / 2 + "px";
      ripple.style.top = clickY - size / 2 + "px";

      // Start the animation
      ripple.classList.add("active");

      // Remove ripple after animation (adjust timing to match CSS animation)
      setTimeout(() => {
        ripple.remove();
      }, 600); // Corresponds to the animation duration in style.css
    });
  });
}

// Apply ripple effect once the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const userInputField = document.getElementById('userInput');
    if (userInputField) {
        userInputField.addEventListener('keypress', function(event) {
            if (event.key === 'Enter') {
                event.preventDefault(); // Prevent default Enter behavior
                sendMessage(); 
            }
        });
    }
    
    applyRippleEffect(); // Initial application for static elements
    
    if (typeof fetchPdfs === 'function') {
        fetchPdfs(); // Initial fetch of PDFs
    }

    // Initialize Drag and Drop
    initializeDragAndDrop();

    // Any other initializations
});

// ===================== DRAG AND DROP FUNCTIONALITY =====================
function initializeDragAndDrop() {
    const body = document.body;
    let dragDropOverlay = document.getElementById('dragDropOverlay');

    // Create overlay if it doesn't exist
    if (!dragDropOverlay) {
        dragDropOverlay = document.createElement('div');
        dragDropOverlay.id = 'dragDropOverlay';
        dragDropOverlay.className = 'drag-drop-overlay';
        
        const overlayContent = document.createElement('div');
        overlayContent.className = 'drag-drop-overlay-content';
        
        const icon = document.createElement('span');
        icon.className = 'material-icons';
        icon.textContent = 'upload_file';
        
        const text = document.createElement('p');
        text.textContent = 'Déposez les fichiers ici';
        
        overlayContent.appendChild(icon);
        overlayContent.appendChild(text);
        dragDropOverlay.appendChild(overlayContent);
        body.appendChild(dragDropOverlay);
    }

    let dragCounter = 0; // To handle nested dragenter/dragleave events

    body.addEventListener('dragenter', (e) => {
        e.preventDefault();
        e.stopPropagation();
        dragCounter++;
        // Only show overlay if dataTransfer contains files
        if (e.dataTransfer && e.dataTransfer.types.includes('Files')) {
            dragDropOverlay.classList.add('active');
        }
    });

    body.addEventListener('dragleave', (e) => {
        e.preventDefault();
        e.stopPropagation();
        dragCounter--;
        if (dragCounter === 0) {
            dragDropOverlay.classList.remove('active');
        }
    });

    body.addEventListener('dragover', (e) => {
        e.preventDefault(); // Necessary to allow drop
        e.stopPropagation();
        // Can add visual cues here if needed, but overlay handles most of it
        if (e.dataTransfer && e.dataTransfer.types.includes('Files')) {
             e.dataTransfer.dropEffect = 'copy'; // Show a copy icon
        }
    });

    body.addEventListener('drop', (e) => {
        e.preventDefault();
        e.stopPropagation();
        dragDropOverlay.classList.remove('active');
        dragCounter = 0;

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            // Pass files to the existing upload mechanism
            handleFileUpload(files);
        }
    });
}

function handleFileUpload(files) {
    const uploadForm = document.getElementById('uploadForm');
    const fileInput = document.getElementById('fileInput');
    const uploadStatus = document.getElementById('uploadStatus');

    // Create a new FormData object and append files
    var formData = new FormData();
    if (files.length === 0) {
        uploadStatus.textContent = "Aucun fichier sélectionné.";
        uploadStatus.style.color = "var(--current-error)";
        return;
    }
    for (var i = 0; i < files.length; i++) {
        // Basic file type check (can be expanded)
        if (!['.pdf', '.txt', '.md', '.csv'].some(ext => files[i].name.toLowerCase().endsWith(ext))) {
            uploadStatus.textContent = `Format non supporté pour ${files[i].name}.`;
            uploadStatus.style.color = "var(--current-error)";
            // Potentially skip this file or stop the whole upload
            // For now, we'll just show a message and continue with other valid files if any
            // Or, to be stricter, you could return here.
            // return;
            continue; // Skip this file
        }
        formData.append("file", files[i]);
    }

    // If after filtering, no valid files are left
    if (!formData.has("file")) {
        uploadStatus.textContent = "Aucun fichier valide sélectionné.";
        uploadStatus.style.color = "var(--current-error)";
        return;
    }

    uploadStatus.textContent = "Envoi en cours...";
    uploadStatus.style.color = "var(--current-secondary)"; // Use theme color

    fetch("/upload", {
        method: "POST",
        body: formData,
    })
    .then((response) => response.json())
    .then((data) => {
        if (data.success) {
            uploadStatus.textContent = "Fichier(s) ingéré(s) avec succès !";
            uploadStatus.style.color = "var(--current-primary)"; // Use theme color
            fetchPdfs(); // Refresh PDF list
        } else {
            uploadStatus.textContent = data.message || "Erreur lors de l'ingestion.";
            uploadStatus.style.color = "var(--current-error)";
        }
    })
    .catch((error) => {
        console.error('Error during upload:', error);
        uploadStatus.textContent = "Erreur lors de l'envoi.";
        uploadStatus.style.color = "var(--current-error)";
    });

    // Clear the file input visually if needed, though drag/drop doesn't use it directly
    if (fileInput) {
        fileInput.value = ''; 
    }
}

// Modify the existing uploadForm event listener to use handleFileUpload
document.addEventListener('DOMContentLoaded', () => {
    // ... (other DOMContentLoaded code like userInput keypress, applyRippleEffect, fetchPdfs)

    const uploadForm = document.getElementById('uploadForm');
    if (uploadForm) {
        uploadForm.addEventListener("submit", function (e) {
            e.preventDefault();
            const files = document.getElementById("fileInput").files;
            handleFileUpload(files);
        });
    }
    
    initializeDragAndDrop();
});

let activeReplyContext = null; // To store the original message text for reply
let currentReplyUI = null; // To store the DOM element of the current reply UI

function showReplyUI(originalMarkdownText) {
    if (currentReplyUI) {
        if (activeReplyContext === originalMarkdownText) {
            document.getElementById('userInput').focus();
            return;
        }
        clearReplyContext(true); // Immediate clear for re-opening
    }

    activeReplyContext = originalMarkdownText;
    const replyContextArea = document.getElementById('reply-context-area');
    replyContextArea.innerHTML = ''; // Clear previous content immediately

    const container = document.createElement('div');
    container.className = 'reply-compact-container';

    const header = document.createElement('div');
    header.className = 'reply-compact-header';
    const title = document.createElement('span');
    title.className = 'reply-to-label';
    const replyIcon = document.createElement('span');
    replyIcon.className = 'material-icons';
    replyIcon.textContent = 'reply';
    title.appendChild(replyIcon);
    title.appendChild(document.createTextNode('Répondre à :'));
    header.appendChild(title);
    const closeBtn = document.createElement('button');
    closeBtn.className = 'reply-close-btn ripple-effect-container';
    closeBtn.title = 'Annuler la réponse (Echap)';
    const closeIcon = document.createElement('span');
    closeIcon.className = 'material-icons';
    closeIcon.textContent = 'close';
    closeBtn.appendChild(closeIcon);
    closeBtn.onclick = (e) => {
        e.stopPropagation();
        clearReplyContext();
    };
    header.appendChild(closeBtn);
    container.appendChild(header);

    const originalMsgDiv = document.createElement('div');
    originalMsgDiv.className = 'reply-compact-original-message';
    originalMsgDiv.textContent = stripMarkdown(originalMarkdownText).substring(0, 100) + (originalMarkdownText.length > 100 ? '...' : '');
    container.appendChild(originalMsgDiv);

    replyContextArea.appendChild(container);
    currentReplyUI = container;

    // Force reflow before adding class to ensure transition plays
    void replyContextArea.offsetWidth;

    requestAnimationFrame(() => {
        replyContextArea.classList.add('reply-context-active');
    });

    document.getElementById('userInput').focus();
    if (typeof applyRippleEffect === 'function') {
        applyRippleEffect();
    }
    document.addEventListener('keydown', handleEscapeForReply);
}

function clearReplyContext(immediate = false) {
    activeReplyContext = null;
    const replyContextArea = document.getElementById('reply-context-area');

    if (immediate) {
        replyContextArea.classList.remove('reply-context-active');
        replyContextArea.innerHTML = '';
        currentReplyUI = null;
    } else {
        replyContextArea.classList.remove('reply-context-active');
        // CSS handles content fade-out via .reply-compact-container opacity transition
        // when .reply-context-active is removed from replyContextArea.
        // setTimeout ensures innerHTML is cleared after the container's transition (max-height, padding etc.)
        setTimeout(() => {
            if (!replyContextArea.classList.contains('reply-context-active') && currentReplyUI) {
                replyContextArea.innerHTML = '';
                currentReplyUI = null;
            }
        }, 250); // Should match the longest transition duration on .reply-context-area (e.g., max-height)
    }

    document.removeEventListener('keydown', handleEscapeForReply);
}

function handleEscapeForReply(event) {
    if (event.key === 'Escape') {
        if (activeReplyContext) { // Check if reply UI is active
            clearReplyContext();
        }
    }
}

/* ... sendMessage and other functions remain largely the same ... */
/* Ensure the sendMessage function correctly uses activeReplyContext and calls clearReplyContext */

// Example of where applyRippleEffect might be called if it's not global or on DOMContentLoaded
// document.addEventListener('DOMContentLoaded', () => { applyRippleEffect(); });
