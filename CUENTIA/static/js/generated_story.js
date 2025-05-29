/**
 * Generated Story JavaScript - AUDIO SIMPLIFICADO
 * Un solo botón para escuchar el cuento
 */

// Variables globales
let currentUtterance = null
let isPlaying = false

/**
 * Inicialización
 */
document.addEventListener("DOMContentLoaded", () => {
  console.log("🚀 Inicializando cuento...")

  setupEventListeners()
  animateElements()

  // Verificar TTS
  if ("speechSynthesis" in window) {
    console.log("✅ TTS disponible")
  } else {
    console.error("❌ TTS no disponible")
    mostrarMensaje("⚠️ Tu navegador no soporta síntesis de voz", "error")
  }

  setTimeout(() => {
    mostrarMensaje("✨ ¡Cuento listo para leer!", "success")
  }, 1000)
})

/**
 * Configurar event listeners
 */
function setupEventListeners() {
  const audioBtn = document.getElementById("audio-btn")
  if (audioBtn) {
    audioBtn.addEventListener("click", toggleAudio)
  }
}

/**
 * ALTERNAR AUDIO (Play/Stop)
 */
function toggleAudio() {
  if (isPlaying) {
    stopStory()
  } else {
    playStory()
  }
}

/**
 * REPRODUCIR CUENTO
 */
function playStory() {
  console.log("▶️ Iniciando reproducción...")

  if (!window.speechSynthesis) {
    mostrarMensaje("❌ Tu navegador no soporta síntesis de voz", "error")
    return
  }

  // Obtener texto del cuento
  const storyElement = document.getElementById("story-content")
  const moralejaElement = document.getElementById("moraleja-content")

  let fullText = ""
  if (storyElement) {
    fullText += storyElement.innerText || storyElement.textContent
  }
  if (moralejaElement && moralejaElement.textContent.trim()) {
    fullText += "\n\n" + (moralejaElement.innerText || moralejaElement.textContent)
  }

  if (!fullText.trim()) {
    mostrarMensaje("❌ No hay texto para reproducir", "error")
    return
  }

  console.log("📝 Reproduciendo cuento...")

  // Crear utterance
  currentUtterance = new SpeechSynthesisUtterance(fullText)

  // Configurar voz en español
  currentUtterance.lang = "es-ES"
  currentUtterance.rate = 0.8
  currentUtterance.pitch = 1.0
  currentUtterance.volume = 1.0

  // Buscar voz en español
  const voices = window.speechSynthesis.getVoices()
  const spanishVoice = voices.find((voice) => voice.lang.startsWith("es"))

  if (spanishVoice) {
    currentUtterance.voice = spanishVoice
    console.log("🎤 Voz:", spanishVoice.name)
  }

  // Eventos
  currentUtterance.onstart = () => {
    console.log("✅ Reproducción iniciada")
    isPlaying = true
    updateAudioButton()
    mostrarMensaje("🎧 Escuchando cuento...", "info")
  }

  currentUtterance.onend = () => {
    console.log("✅ Reproducción completada")
    isPlaying = false
    updateAudioButton()
    mostrarMensaje("✅ Cuento terminado", "success")
  }

  currentUtterance.onerror = (event) => {
    console.error("❌ Error TTS:", event)
    isPlaying = false
    updateAudioButton()
    mostrarMensaje(" AUDIO DETENIDO", "error")
  }

  // Iniciar reproducción
  window.speechSynthesis.speak(currentUtterance)
}

/**
 * DETENER CUENTO
 */
function stopStory() {
  console.log("⏹️ Deteniendo reproducción...")

  window.speechSynthesis.cancel()
  isPlaying = false
  currentUtterance = null
  updateAudioButton()
  mostrarMensaje("⏹️ Audio detenido", "info")
}

/**
 * ACTUALIZAR BOTÓN DE AUDIO
 */
function updateAudioButton() {
  const audioBtn = document.getElementById("audio-btn")

  if (audioBtn) {
    if (isPlaying) {
      audioBtn.textContent = "⏹️ Detener Audio"
      audioBtn.className = "btn-action btn-danger"
    } else {
      audioBtn.textContent = "🎧 Escuchar Cuento"
      audioBtn.className = "btn-action btn-audio"
    }
  }
}

/**
 * DETENER AUDIO AL CAMBIAR DE PÁGINA
 */
function stopAudioOnPageChange() {
  if (window.speechSynthesis && isPlaying) {
    console.log("🔄 Deteniendo audio por cambio de página...")
    window.speechSynthesis.cancel()
    isPlaying = false
    currentUtterance = null
  }
}

/**
 * Event listeners para detectar cambio de página
 */
window.addEventListener("beforeunload", stopAudioOnPageChange)
window.addEventListener("pagehide", stopAudioOnPageChange)

// Detener audio cuando se hace clic en enlaces
document.addEventListener("click", (event) => {
  const target = event.target

  // Si es un enlace que va a otra página
  if (target.tagName === "A" && target.href && !target.href.includes("#")) {
    stopAudioOnPageChange()
  }

  // Si es un botón que puede redirigir
  if (target.tagName === "BUTTON" && target.type === "submit") {
    stopAudioOnPageChange()
  }
})

/**
 * Mostrar mensajes
 */
function mostrarMensaje(mensaje, tipo = "info") {
  console.log(`📢 ${tipo.toUpperCase()}: ${mensaje}`)

  const messageDiv = document.createElement("div")

  let backgroundColor
  switch (tipo) {
    case "success":
      backgroundColor = "#8b5cf6"
      break
    case "error":
      backgroundColor = "#EF4444"
      break
    default:
      backgroundColor = "#9481dd"
  }

  messageDiv.style.cssText = `
    position: fixed;
    top: 2rem;
    right: 2rem;
    background: ${backgroundColor};
    color: white;
    padding: 1rem 1.5rem;
    border-radius: 12px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.2);
    z-index: 1000;
    font-weight: 600;
    max-width: 300px;
    word-wrap: break-word;
  `

  messageDiv.textContent = mensaje
  document.body.appendChild(messageDiv)

  setTimeout(() => {
    if (document.body.contains(messageDiv)) {
      document.body.removeChild(messageDiv)
    }
  }, 3000)
}

/**
 * Animar elementos
 */
function animateElements() {
  const elements = document.querySelectorAll(".story-text, .story-image, .btn-action")

  elements.forEach((el, index) => {
    el.style.opacity = "0"
    el.style.transform = "translateY(20px)"

    setTimeout(() => {
      el.style.transition = "all 0.6s ease-out"
      el.style.opacity = "1"
      el.style.transform = "translateY(0)"
    }, index * 100)
  })
}

console.log("✅ Script de audio simplificado cargado")
