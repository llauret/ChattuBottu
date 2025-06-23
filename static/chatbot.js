// ===================== SESSION TRACKING =====================
class SessionTracker {
  constructor() {
    this.sessionId = null;
    this.sessionStartTime = null;
    this.qcmStartTime = null;
    this.init();
  }
  
  async init() {
    try {
      const response = await fetch('/dashboard/session/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      const result = await response.json();
      if (result.success) {
        this.sessionId = result.session_id;
        this.sessionStartTime = Date.now();
        console.log('Session démarrée:', this.sessionId);
      }
    } catch (error) {
      console.error('Erreur lors du démarrage de session:', error);
    }
  }
  
  async trackActivity(activity, document = null) {
    try {
      await fetch('/dashboard/activity', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          activity: activity,
          document: document
        })
      });
    } catch (error) {
      console.error('Erreur lors du tracking:', error);
    }
  }
  
  startQCM() {
    this.qcmStartTime = Date.now();
    this.trackActivity('qcm');
  }
  
  async completeQCM(qcmData) {
    const completionTime = this.qcmStartTime ? (Date.now() - this.qcmStartTime) / 1000 : null;
    
    try {
      await fetch('/dashboard/qcm/complete', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          ...qcmData,
          completion_time: completionTime
        })
      });
    } catch (error) {
      console.error('Erreur lors du tracking QCM:', error);
    }
  }
  
  async endSession() {
    try {
      await fetch('/dashboard/session/end', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });
    } catch (error) {
      console.error('Erreur lors de la fin de session:', error);
    }
  }
}

// Instance globale du tracker
const sessionTracker = new SessionTracker();

// Terminer la session lors de la fermeture de la page
window.addEventListener('beforeunload', () => {
  sessionTracker.endSession();
});

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
  
  // Tracker l'activité de chat
  sessionTracker.trackActivity('chat');
  
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
      
      // Ajouter le titre de la section s'il y a des fichiers
      if (data.pdfs && data.pdfs.length > 0) {
        var titleDiv = document.createElement("div");
        titleDiv.className = "pdf-list-title";
        titleDiv.innerHTML = '<span class="material-icons">folder</span> Documents ingérés';
        pdfList.appendChild(titleDiv);
        
        var listContainer = document.createElement("div");
        listContainer.className = "pdf-list";
        
        data.pdfs.forEach((pdf) => {
          var item = document.createElement("div");
          item.className = "pdf-item";
          
          var info = document.createElement("div");
          info.className = "pdf-info";
          
          var icon = document.createElement("span");
          icon.className = "material-icons pdf-icon";
          icon.textContent = "picture_as_pdf";
          
          var details = document.createElement("div");
          details.className = "pdf-details";
          
          var name = document.createElement("div");
          name.className = "pdf-name";
          name.textContent = pdf;
          
          var meta = document.createElement("div");
          meta.className = "pdf-meta";
          meta.innerHTML = '<span>Document</span>';
          
          details.appendChild(name);
          details.appendChild(meta);
          
          info.appendChild(icon);
          info.appendChild(details);
          
          var actions = document.createElement("div");
          actions.className = "pdf-actions";
          
          var delBtn = document.createElement("button");
          delBtn.className = "pdf-action-btn delete ripple-effect-container";
          delBtn.title = "Supprimer le fichier";
          
          var delIcon = document.createElement("span");
          delIcon.classList.add("material-icons");
          delIcon.textContent = "delete";
          delBtn.appendChild(delIcon);
          
          delBtn.onclick = function () {
            deletePdf(pdf);
          };
          
          actions.appendChild(delBtn);
          
          item.appendChild(info);
          item.appendChild(actions);
          listContainer.appendChild(item);
        });
        
        pdfList.appendChild(listContainer);
      } else {
        var emptyState = document.createElement("div");
        emptyState.className = "pdf-empty-state";
        emptyState.innerHTML = '<div class="pdf-empty-icon"><span class="material-icons">folder_open</span></div><div>Aucun document ingéré</div>';
        pdfList.appendChild(emptyState);
      }
      
      // Re-apply ripple effect to newly added buttons if not using event delegation
      if (typeof applyRippleEffect === 'function') {
        applyRippleEffect(); 
      }
    })
    .catch(error => {
      console.error("Error fetching PDF list:", error);
      var pdfList = document.getElementById("pdfList");
      var errorState = document.createElement("div");
      errorState.className = "pdf-empty-state";
      errorState.innerHTML = '<div class="pdf-empty-icon"><span class="material-icons">error</span></div><div>Erreur au chargement des documents</div>';
      pdfList.appendChild(errorState);
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
    initializeDragAndDrop();    // Event listener pour le bouton de génération de fiches de révision
    const generateRevisionBtn = document.getElementById("generateRevisionBtn");
    if (generateRevisionBtn) {
      generateRevisionBtn.addEventListener("click", generateRevisionSheet);
    }
    
    // Event listener pour le bouton de génération de QCM
    const generateQCMBtn = document.getElementById("generateQCMBtn");
    if (generateQCMBtn) {
      generateQCMBtn.addEventListener("click", generateQCM);
    }
    
    // Charger la liste des QCM au démarrage
    refreshQCMList();
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
    .then((response) => response.json())    .then((data) => {
        if (data.success) {
            uploadStatus.textContent = "Fichier(s) ingéré(s) avec succès !";
            uploadStatus.style.color = "var(--current-primary)"; // Use theme color
            fetchPdfs(); // Refresh PDF list
            
            // Tracker l'activité d'upload de documents
            for (let i = 0; i < files.length; i++) {
                sessionTracker.trackActivity('document_upload', files[i].name);
            }
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

// ===================== REVISION SHEET GENERATION =====================
function generateRevisionSheet() {
  const btn = document.getElementById("generateRevisionBtn");
  const status = document.getElementById("revisionStatus");
  
  btn.disabled = true;
  btn.innerHTML = '<span class="material-icons">hourglass_empty</span> Génération...';
  status.textContent = "Génération de la fiche de révision en cours...";
  status.className = "revision-status loading";
  
  // Tracker l'activité de génération de révision
  sessionTracker.trackActivity('revision_generation');
  
  fetch("/generate_revision_sheet", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({})
  })
  .then(response => response.json())
  .then(data => {
    btn.disabled = false;
    btn.innerHTML = '<span class="material-icons">description</span> Générer une fiche de révision';
    
    if (data.success) {
      status.textContent = "Fiche de révision générée avec succès !";
      status.className = "revision-status success";
      displayRevisionSheet(data.content);
    } else {
      status.textContent = "Erreur lors de la génération.";
      status.className = "revision-status error";
    }
  })
  .catch(error => {
    btn.disabled = false;
    btn.innerHTML = '<span class="material-icons">description</span> Générer une fiche de révision';
    status.textContent = "Erreur de connexion.";
    status.className = "revision-status error";
    console.error("Error:", error);
  });
}

function displayRevisionSheet(content) {
  // Afficher la fiche dans le chat comme un message spécial
  var chatbox = document.getElementById("chatbox");
  var messageDiv = document.createElement("div");
  messageDiv.classList.add("message", "revision-message");
  
  var icon = document.createElement("span");
  icon.classList.add("icon");
  icon.innerHTML = '<span class="material-icons">description</span>';
  messageDiv.appendChild(icon);
  
  var textSpan = document.createElement("span");
  textSpan.innerHTML = window.marked.parse(content);
  messageDiv.appendChild(textSpan);
  
  // Ajout du bouton TTS pour la fiche
  var ttsBtn = document.createElement("button");
  ttsBtn.className = "tts-btn";
  ttsBtn.title = "Lire la fiche de révision";
  ttsBtn.innerHTML = '<span class="material-icons">volume_up</span>';
  ttsBtn.onclick = function () {
    ttsBtn.classList.add("playing");
    speakText(stripMarkdown(content), function() {
      ttsBtn.classList.remove("playing");
    });
  };
  messageDiv.appendChild(ttsBtn);
  
  chatbox.appendChild(messageDiv);
  chatbox.scrollTop = chatbox.scrollHeight;
}

// ===================== QCM FUNCTIONALITY =====================
let currentQCM = null;
let currentQuestionIndex = 0;
let userAnswers = [];

function generateQCM() {
  const btn = document.getElementById("generateQCMBtn");
  const status = document.getElementById("qcmStatus");
  const numQuestions = document.getElementById("numQuestions").value;
  
  btn.disabled = true;
  btn.innerHTML = '<span class="material-icons">hourglass_empty</span> Génération...';
  status.textContent = "Génération du QCM en cours...";
  status.className = "qcm-status loading";
  
  // Tracker l'activité de génération de QCM
  sessionTracker.trackActivity('qcm_generation');
  
  fetch("/qcm/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ num_questions: parseInt(numQuestions) })
  })
  .then(response => response.json())
  .then(data => {
    btn.disabled = false;
    btn.innerHTML = '<span class="material-icons">add_circle</span> Créer un QCM';
    
    if (data.success) {
      status.textContent = "QCM généré avec succès !";
      status.className = "qcm-status success";
      currentQCM = data.qcm;
      userAnswers = new Array(data.qcm.questions.length).fill(-1);
      currentQuestionIndex = 0;
      refreshQCMList();
      // Démarrer le tracking du QCM
      sessionTracker.startQCM();
      openQCM(data.qcm);
    } else {
      status.textContent = data.error || "Erreur lors de la génération.";
      status.className = "qcm-status error";
    }
  })
  .catch(error => {
    btn.disabled = false;
    btn.innerHTML = '<span class="material-icons">add_circle</span> Créer un QCM';
    status.textContent = "Erreur de connexion.";
    status.className = "qcm-status error";
    console.error("Error:", error);
  });
}

function openQCM(qcm) {
  currentQCM = qcm;
  currentQuestionIndex = 0;
  userAnswers = new Array(qcm.questions.length).fill(-1);
  
  document.getElementById("qcmTitle").textContent = qcm.title;
  document.getElementById("qcmModal").style.display = "flex";
  updateQCMDisplay();
}

function closeQCM() {
  document.getElementById("qcmModal").style.display = "none";
  currentQCM = null;
  currentQuestionIndex = 0;
  userAnswers = [];
}

function updateQCMDisplay() {
  if (!currentQCM) return;
  
  const question = currentQCM.questions[currentQuestionIndex];
  const progressPercent = ((currentQuestionIndex + 1) / currentQCM.questions.length) * 100;
  
  // Mise à jour de la barre de progression
  document.getElementById("qcmProgressFill").style.width = progressPercent + "%";
  document.getElementById("qcmProgressText").textContent = 
    `Question ${currentQuestionIndex + 1} / ${currentQCM.questions.length}`;
  
  // Affichage de la question
  const content = document.getElementById("qcmContent");
  content.innerHTML = `
    <div class="qcm-question">
      <h3>${question.question}</h3>
      <div class="qcm-options">
        ${question.options.map((option, index) => `
          <label class="qcm-option ${userAnswers[currentQuestionIndex] === index ? 'selected' : ''}">
            <input type="radio" name="qcm-answer" value="${index}" 
                   ${userAnswers[currentQuestionIndex] === index ? 'checked' : ''}
                   onchange="selectAnswer(${index})">
            <span class="qcm-option-text">${String.fromCharCode(65 + index)}. ${option}</span>
          </label>
        `).join('')}
      </div>
    </div>
  `;
  
  // Mise à jour des boutons de navigation
  document.getElementById("qcmPrevBtn").disabled = currentQuestionIndex === 0;
  
  if (currentQuestionIndex === currentQCM.questions.length - 1) {
    document.getElementById("qcmNextBtn").style.display = "none";
    document.getElementById("qcmSubmitBtn").style.display = "inline-flex";
  } else {
    document.getElementById("qcmNextBtn").style.display = "inline-flex";
    document.getElementById("qcmSubmitBtn").style.display = "none";
  }
}

function selectAnswer(answerIndex) {
  userAnswers[currentQuestionIndex] = answerIndex;
  
  // Mise à jour visuelle
  const options = document.querySelectorAll('.qcm-option');
  options.forEach((option, index) => {
    option.classList.toggle('selected', index === answerIndex);
  });
}

function previousQuestion() {
  if (currentQuestionIndex > 0) {
    currentQuestionIndex--;
    updateQCMDisplay();
  }
}

function nextQuestion() {
  if (currentQuestionIndex < currentQCM.questions.length - 1) {
    currentQuestionIndex++;
    updateQCMDisplay();
  }
}

function submitQCM() {
  if (!currentQCM) return;
  
  // Vérifier que toutes les questions ont une réponse
  const unanswered = userAnswers.findIndex(answer => answer === -1);
  if (unanswered !== -1) {
    alert(`Veuillez répondre à la question ${unanswered + 1}.`);
    currentQuestionIndex = unanswered;
    updateQCMDisplay();
    return;
  }
  
  // Soumettre les réponses
  fetch("/qcm/submit", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      qcm_id: currentQCM.id,
      answers: userAnswers
    })
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      // Tracker la completion du QCM
      sessionTracker.completeQCM({
        qcm_id: currentQCM.id,
        qcm_title: currentQCM.title,
        user_answers: userAnswers,
        score: data.result.score,
        total_questions: data.result.total_questions,
        percentage: data.result.percentage,
        details: data.result.details
      });
      
      closeQCM();
      showQCMResults(data.result);
    } else {
      alert("Erreur lors de la soumission : " + data.error);
    }
  })
  .catch(error => {
    alert("Erreur de connexion lors de la soumission.");
    console.error("Error:", error);
  });
}

function showQCMResults(result) {
  const modal = document.getElementById("qcmResultsModal");
  const content = document.getElementById("qcmResultsContent");
  
  const scoreColor = result.percentage >= 80 ? '#4caf50' : 
                    result.percentage >= 60 ? '#ff9800' : '#f44336';
  
  content.innerHTML = `
    <div class="qcm-score">
      <div class="qcm-score-circle" style="border-color: ${scoreColor};">
        <span class="qcm-score-text" style="color: ${scoreColor};">
          ${result.score}/${result.total_questions}
        </span>
        <span class="qcm-score-percent" style="color: ${scoreColor};">
          ${result.percentage}%
        </span>
      </div>
    </div>
    
    <div class="qcm-details">
      <h3>Détail des réponses</h3>
      ${result.details.map((detail, index) => `
        <div class="qcm-detail-item ${detail.is_correct ? 'correct' : 'incorrect'}">
          <div class="qcm-detail-question">
            <strong>Question ${index + 1}:</strong> ${detail.question}
          </div>
          <div class="qcm-detail-answers">
            <div class="qcm-detail-answer">
              <span class="material-icons">${detail.is_correct ? 'check_circle' : 'cancel'}</span>
              <strong>Votre réponse:</strong> ${String.fromCharCode(65 + detail.user_answer)}. ${detail.options[detail.user_answer]}
            </div>
            ${!detail.is_correct ? `
              <div class="qcm-detail-answer correct-answer">
                <span class="material-icons">check_circle</span>
                <strong>Bonne réponse:</strong> ${String.fromCharCode(65 + detail.correct_answer)}. ${detail.options[detail.correct_answer]}
              </div>
            ` : ''}
          </div>
          <div class="qcm-detail-explanation">
            <strong>Explication:</strong> ${detail.explanation}
          </div>
        </div>
      `).join('')}
    </div>
  `;
  
  modal.style.display = "flex";
}

function closeQCMResults() {
  document.getElementById("qcmResultsModal").style.display = "none";
}

function refreshQCMList() {
  fetch("/qcm/list")
  .then(response => response.json())
  .then(data => {
    const qcmList = document.getElementById("qcmList");
    if (data.success && data.qcms.length > 0) {
      qcmList.innerHTML = `
        <h4>QCM disponibles</h4>
        ${data.qcms.map(qcm => `
          <div class="qcm-item">
            <div class="qcm-item-info">
              <span class="qcm-item-title">${qcm.title}</span>
              <span class="qcm-item-meta">${qcm.total_questions} questions</span>
            </div>
            <button class="qcm-item-btn" onclick="startExistingQCM('${qcm.id}')">
              <span class="material-icons">play_arrow</span>
            </button>
          </div>
        `).join('')}
      `;
    } else {
      qcmList.innerHTML = '<div class="qcm-item-empty">Aucun QCM disponible</div>';
    }
  })
  .catch(error => {
    console.error("Error fetching QCM list:", error);
  });
}

function startExistingQCM(qcmId) {
  // Charger un QCM existant et l'afficher
  fetch(`/qcm/get/${qcmId}`)
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        // Réinitialiser l'état du QCM pour un nouveau passage
        currentQCM = data.qcm;
        userAnswers = new Array(data.qcm.questions.length).fill(-1);
        currentQuestionIndex = 0;
        
        // Ouvrir le QCM dans le modal
        openQCM(data.qcm);
      } else {
        alert("Erreur lors du chargement du QCM : " + (data.error || "Erreur inconnue"));
      }
    })
    .catch(error => {
      console.error("Erreur lors du chargement du QCM:", error);
      alert("Erreur de connexion lors du chargement du QCM");
    });
}

// ===================== DASHBOARD MODAL FUNCTIONS =====================

function openDashboardModal() {
  console.log('Ouverture du dashboard modal');
  const modal = document.getElementById('dashboardModal');
  const content = document.getElementById('dashboardContent');
  
  // Afficher la modal
  modal.style.display = 'flex';
  
  // Charger le contenu du dashboard
  loadDashboardContent();
}

function closeDashboardModal() {
  const modal = document.getElementById('dashboardModal');
  modal.style.display = 'none';
}

function loadDashboardContent() {
  const content = document.getElementById('dashboardContent');
  
  // Afficher le spinner de chargement
  content.innerHTML = `
    <div class="loading-spinner">
      <span class="material-icons rotating">refresh</span>
      <p>Chargement des statistiques...</p>
    </div>
  `;
    // Charger les données du dashboard
  fetch('/dashboard/data')
    .then(response => response.json())
    .then(result => {
        console.log('Dashboard chargé avec succès', result)
      if (result.success) {
        displayDashboardContent(result.data);
      } else {
        throw new Error(result.error || 'Erreur inconnue');
      }
    })
    .catch(error => {
      console.error('Erreur lors du chargement du dashboard:', error);
      content.innerHTML = `
        <div class="error-message">
          <span class="material-icons">error</span>
          <p>Erreur lors du chargement des statistiques.</p>
          <button class="retry-btn" onclick="loadDashboardContent()">
            <span class="material-icons">refresh</span>
            Réessayer
          </button>
        </div>
      `;
    });
}

function displayDashboardContent(data) {
  const content = document.getElementById('dashboardContent');
  
  content.innerHTML = `
    <div class="dashboard-overview">
      <div class="dashboard-stats-grid">
        <div class="stat-card">
          <div class="stat-icon">
            <span class="material-icons">quiz</span>
          </div>
          <div class="stat-content">
            <h3>${data.total_qcm || 0}</h3>
            <p>QCM Complétés</p>
          </div>
        </div>
        
        <div class="stat-card">
          <div class="stat-icon">
            <span class="material-icons">school</span>
          </div>
          <div class="stat-content">
            <h3>${data.average_score || 0}%</h3>
            <p>Score Moyen</p>
          </div>
        </div>
        
        <div class="stat-card">
          <div class="stat-icon">
            <span class="material-icons">chat</span>
          </div>
          <div class="stat-content">
            <h3>${data.total_messages || 0}</h3>
            <p>Messages Échangés</p>
          </div>
        </div>
        
        <div class="stat-card">
          <div class="stat-icon">
            <span class="material-icons">description</span>
          </div>
          <div class="stat-content">
            <h3>${data.total_files || 0}</h3>
            <p>Fichiers Ingérés</p>
          </div>
        </div>
      </div>
      
      <div class="dashboard-charts">
        <div class="chart-container">
          <h3>Progression des Scores</h3>
          <canvas id="scoreChart" width="400" height="200"></canvas>
        </div>
        
        <div class="chart-container">
          <h3>Activité Récente</h3>
          <div class="activity-list">
            ${data.recent_activities ? data.recent_activities.map(activity => `
              <div class="activity-item">
                <span class="material-icons">${getActivityIcon(activity.type)}</span>
                <div class="activity-content">
                  <p>${activity.description}</p>
                  <small>${formatDate(activity.timestamp)}</small>
                </div>
              </div>
            `).join('') : '<p>Aucune activité récente</p>'}
          </div>
        </div>
      </div>
      
      <div class="dashboard-recommendations">
        <h3>Recommandations</h3>
        <div class="recommendations-list">
          ${data.recommendations ? data.recommendations.map(rec => `
            <div class="recommendation-item">
              <span class="material-icons">${rec.icon}</span>
              <div class="recommendation-content">
                <h4>${rec.title}</h4>
                <p>${rec.description}</p>
              </div>
            </div>
          `).join('') : '<p>Aucune recommandation disponible</p>'}
        </div>
      </div>
    </div>
  `;
  
  // Initialiser les graphiques si Chart.js est disponible
  if (typeof Chart !== 'undefined' && data.score_history) {
    initializeScoreChart(data.score_history);
  }
}

function getActivityIcon(type) {
  switch(type) {
    case 'qcm': return 'quiz';
    case 'chat': return 'chat';
    case 'upload': return 'upload_file';
    case 'revision': return 'school';
    default: return 'info';
  }
}

function formatDate(dateString) {
  const date = new Date(dateString);
  return date.toLocaleDateString('fr-FR', { 
    year: 'numeric', 
    month: 'short', 
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

function initializeScoreChart(scoreHistory) {
  const ctx = document.getElementById('scoreChart').getContext('2d');
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: scoreHistory.map(item => formatDate(item.date)),
      datasets: [{
        label: 'Score (%)',
        data: scoreHistory.map(item => item.score),
        borderColor: 'var(--current-primary)',
        backgroundColor: 'var(--current-primary-container)',
        tension: 0.1
      }]
    },
    options: {
      responsive: true,
      scales: {
        y: {
          beginAtZero: true,
          max: 100
        }
      }
    }
  });
}

// Fermer la modal en cliquant à l'extérieur
document.addEventListener('click', function(event) {
  const dashboardModal = document.getElementById('dashboardModal');
  if (event.target === dashboardModal) {
    closeDashboardModal();
  }
});
