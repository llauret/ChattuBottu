/**
 * Code Sandbox - Exécution de code Python dans le navigateur avec Brython
 * Version simplifiée et fonctionnelle
 */

class CodeSandbox {
    constructor() {
        this.brythonLoaded = false;
        this.loadBrython();
    }
    
    async loadBrython() {
        try {
            // Charger Brython si pas déjà fait
            if (!window.brython) {
                await this.loadScript('https://cdn.jsdelivr.net/npm/brython@3/brython.min.js');
                await this.loadScript('https://cdn.jsdelivr.net/npm/brython@3/brython_stdlib.js');
            }
            
            // Initialiser Brython une seule fois
            if (typeof window.brython === 'function' && !window.__brython_initialized) {
                window.brython({ debug: 1, pythonpath: ['.', '/'] });
                window.__brython_initialized = true;
            }
            
            this.brythonLoaded = true;
            console.log('Brython chargé avec succès');
        } catch (error) {
            console.error('Erreur lors du chargement de Brython:', error);
            // Fallback sans Brython
            this.setupFallback();
        }
    }
    
    setupFallback() {
        console.log('Utilisation du mode fallback (simulation)');
        this.brythonLoaded = true; // Pour permettre l'exécution en mode simulation
    }
    
    loadScript(src) {
        return new Promise((resolve, reject) => {
            if (document.querySelector(`script[src="${src}"]`)) {
                resolve();
                return;
            }
            
            const script = document.createElement('script');
            script.src = src;
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }
    
    /**
     * Créer un bloc de code exécutable
     */
    createExecutableCodeBlock(code, language = 'python') {
        const container = document.createElement('div');
        container.className = 'code-block-container';
        
        const header = document.createElement('div');
        header.className = 'code-block-header';
        
        const languageLabel = document.createElement('div');
        languageLabel.className = 'code-block-language';
        languageLabel.innerHTML = `
            <span class="material-icons">code</span>
            <span>${language.toUpperCase()}</span>
        `;
        
        const actions = document.createElement('div');
        actions.className = 'code-block-actions';
        
        // Bouton d'exécution
        const runBtn = document.createElement('button');
        runBtn.className = 'code-action-btn';
        runBtn.innerHTML = `
            <span class="material-icons">play_arrow</span>
            <span>Exécuter</span>
        `;
        runBtn.onclick = () => this.executeCode(container, code);
        
        // Bouton de copie
        const copyBtn = document.createElement('button');
        copyBtn.className = 'code-action-btn';
        copyBtn.innerHTML = `
            <span class="material-icons">content_copy</span>
            <span>Copier</span>
        `;
        copyBtn.onclick = () => this.copyCode(code, copyBtn);
        
        actions.appendChild(runBtn);
        actions.appendChild(copyBtn);
        header.appendChild(languageLabel);
        header.appendChild(actions);
        
        // Contenu du code
        const content = document.createElement('div');
        content.className = 'code-block-content';
        
        const pre = document.createElement('pre');
        const codeElement = document.createElement('code');
        codeElement.textContent = code;
        codeElement.className = `language-${language}`;
        pre.appendChild(codeElement);
        content.appendChild(pre);
        
        container.appendChild(header);
        container.appendChild(content);
        
        // Appliquer la coloration syntaxique si Prism est disponible
        if (window.Prism) {
            window.Prism.highlightElement(codeElement);
        }
        
        return container;
    }
    
    /**
     * Exécuter du code Python
     */
    async executeCode(container, code) {
        if (!this.brythonLoaded) {
            this.showError(container, 'Système d\'exécution en cours de chargement...');
            return;
        }
        
        const runBtn = container.querySelector('.code-action-btn');
        const originalContent = runBtn.innerHTML;
        
        // Indiquer que l'exécution est en cours
        runBtn.innerHTML = `
            <span class="loading-spinner-inline">
                <span class="material-icons">refresh</span>
                <span>Exécution...</span>
            </span>
        `;
        runBtn.disabled = true;
        
        // Supprimer l'ancien output s'il existe
        const existingOutput = container.querySelector('.code-output');
        if (existingOutput) {
            existingOutput.remove();
        }
        
        try {
            let result;
            
            if (window.brython && window.brython.python_to_js) {
                // Méthode Brython
                result = await this.executeBrythonCode(code);
            } else {
                // Méthode fallback (simulation)
                result = this.simulateCodeExecution(code);
            }
            
            this.showOutput(container, result, 'success');
            
        } catch (error) {
            this.showError(container, error.message || 'Erreur lors de l\'exécution');
        } finally {
            // Restaurer le bouton
            runBtn.innerHTML = originalContent;
            runBtn.disabled = false;
        }
    }
    
    /**
     * Exécuter du code avec Brython
     */
    async executeBrythonCode(code) {
        return new Promise((resolve, reject) => {
            try {
                // Variables pour capturer la sortie
                let capturedOutput = '';
                
                // Créer un wrapper JavaScript qui capture print()
                const wrappedCode = `
import sys
from io import StringIO

# Capturer stdout
old_stdout = sys.stdout
captured_output = StringIO()
sys.stdout = captured_output

# Variables pour stocker les résultats
execution_result = None
execution_error = None

try:
    # Code utilisateur
${code.split('\n').map(line => '    ' + line).join('\n')}
    
    # Si pas de print, essayer d'afficher la dernière expression
    output_text = captured_output.getvalue()
    if not output_text.strip():
        # Chercher des variables créées
        user_vars = [f"{k} = {repr(v)}" for k, v in locals().items() 
                    if not k.startswith('_') and k not in ['old_stdout', 'captured_output', 'output_text']]
        if user_vars:
            output_text = "Variables créées:\\n" + "\\n".join(user_vars)
        else:
            output_text = "Code exécuté avec succès"
    
    execution_result = output_text

except Exception as e:
    import traceback
    execution_error = f"Erreur: {str(e)}\\nDétails: {traceback.format_exc()}"

finally:
    sys.stdout = old_stdout

# Retourner le résultat via une fonction globale
from browser import window
if execution_error:
    window.python_execution_callback(None, execution_error)
else:
    window.python_execution_callback(execution_result, None)
`;
                
                // Définir le callback
                window.python_execution_callback = (result, error) => {
                    if (error) {
                        reject(new Error(error));
                    } else {
                        resolve(result || 'Code exécuté avec succès');
                    }
                };
                
                // Exécuter avec Brython
                const jsCode = window.brython.python_to_js(wrappedCode);
                eval(jsCode);
                
                // Timeout de sécurité
                setTimeout(() => {
                    reject(new Error('Timeout - L\'exécution a pris trop de temps'));
                }, 5000);
                
            } catch (error) {
                reject(error);
            }
        });
    }
    
    /**
     * Simuler l'exécution de code (fallback)
     */
    simulateCodeExecution(code) {
        // Simulation simple pour les cas de base
        const lines = code.split('\n').map(line => line.trim()).filter(line => line && !line.startsWith('#'));
        let output = [];
        
        for (const line of lines) {
            if (line.startsWith('print(')) {
                // Extraire le contenu du print
                const match = line.match(/print\((.*)\)/);
                if (match) {
                    let content = match[1];
                    // Supprimer les guillemets
                    if ((content.startsWith('"') && content.endsWith('"')) || 
                        (content.startsWith("'") && content.endsWith("'"))) {
                        content = content.slice(1, -1);
                    }
                    output.push(content);
                }
            } else if (line.includes('=')) {
                // Variable assignment
                const [varName, varValue] = line.split('=').map(s => s.trim());
                if (varValue && !isNaN(varValue)) {
                    output.push(`${varName} = ${varValue}`);
                }
            } else if (line.match(/^\d+\s*[\+\-\*\/]\s*\d+$/)) {
                // Calcul simple
                try {
                    const result = eval(line);
                    output.push(`${line} = ${result}`);
                } catch (e) {
                    // Ignorer les erreurs de calcul
                }
            }
        }
        
        if (output.length === 0) {
            return 'Code exécuté (mode simulation - chargez Brython pour une exécution complète)';
        }
        
        return output.join('\n');
    }
    
    /**
     * Afficher la sortie du code
     */
    showOutput(container, output, type = 'success') {
        const outputDiv = document.createElement('div');
        outputDiv.className = `code-output ${type}`;
        
        if (!output || output.trim() === '') {
            outputDiv.textContent = 'Aucune sortie produite';
            outputDiv.classList.add('empty');
        } else {
            outputDiv.textContent = output;
        }
        
        container.appendChild(outputDiv);
    }
    
    /**
     * Afficher une erreur
     */
    showError(container, error) {
        this.showOutput(container, `${error}`, 'error');
    }
    
    /**
     * Copier le code dans le presse-papiers
     */
    async copyCode(code, button) {
        try {
            await navigator.clipboard.writeText(code);
            
            const originalContent = button.innerHTML;
            button.innerHTML = `
                <span class="material-icons">check</span>
                <span>Copié!</span>
            `;
            
            setTimeout(() => {
                button.innerHTML = originalContent;
            }, 2000);
            
        } catch (error) {
            console.error('Erreur lors de la copie:', error);
            // Fallback pour les navigateurs plus anciens
            this.fallbackCopyTextToClipboard(code);
        }
    }
    
    fallbackCopyTextToClipboard(text) {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {
            document.execCommand('copy');
        } catch (err) {
            console.error('Erreur de copie fallback:', err);
        }
        
        document.body.removeChild(textArea);
    }
}

/**
 * Créer des démonstrations interactives
 */
class InteractiveDemo {
    constructor() {
        this.demos = new Map();
    }
    
    /**
     * Créer une démonstration d'algorithme
     */
    createAlgorithmDemo(title, description, algorithm, inputs) {
        const container = document.createElement('div');
        container.className = 'interactive-demo';
        
        const header = document.createElement('h4');
        header.innerHTML = `
            <span class="material-icons">science</span>
            ${title}
        `;
        
        const desc = document.createElement('p');
        desc.textContent = description;
        
        const controls = document.createElement('div');
        controls.className = 'demo-controls';
        
        // Créer les inputs
        const inputElements = {};
        inputs.forEach(input => {
            const inputEl = document.createElement('input');
            inputEl.type = input.type || 'text';
            inputEl.placeholder = input.placeholder;
            inputEl.value = input.default || '';
            inputEl.className = 'demo-input';
            inputElements[input.name] = inputEl;
            controls.appendChild(inputEl);
        });
        
        // Bouton d'exécution
        const runBtn = document.createElement('button');
        runBtn.className = 'demo-button';
        runBtn.innerHTML = `
            <span class="material-icons">play_arrow</span>
            Tester
        `;
        
        // Zone de résultat
        const result = document.createElement('div');
        result.className = 'demo-result';
        result.style.display = 'none';
        
        runBtn.onclick = () => {
            const values = {};
            Object.keys(inputElements).forEach(key => {
                values[key] = inputElements[key].value;
            });
            
            try {
                const output = algorithm(values);
                result.textContent = output;
                result.style.display = 'block';
            } catch (error) {
                result.textContent = `Erreur: ${error.message}`;
                result.style.display = 'block';
            }
        };
        
        controls.appendChild(runBtn);
        
        container.appendChild(header);
        container.appendChild(desc);
        container.appendChild(controls);
        container.appendChild(result);
        
        return container;
    }
}

// Instances globales
const codeSandbox = new CodeSandbox();
const interactiveDemo = new InteractiveDemo();

/**
 * Fonction pour traiter les réponses markdown et identifier les blocs de code exécutables
 */
function processExecutableCode(content) {
    // Chercher les blocs de code marqués comme exécutables
    const executableCodeRegex = /```python-executable\n([\s\S]*?)\n```/g;
    
    return content.replace(executableCodeRegex, (match, code) => {
        const codeBlock = codeSandbox.createExecutableCodeBlock(code.trim(), 'python');
        const placeholder = document.createElement('div');
        placeholder.appendChild(codeBlock);
        return placeholder.innerHTML;
    });
}

/**
 * Fonction utilitaire pour créer des explications étape par étape
 */
function createStepByStepExplanation(steps) {
    const container = document.createElement('div');
    
    steps.forEach((step, index) => {
        const stepDiv = document.createElement('div');
        stepDiv.className = 'step-explanation';
        
        const title = document.createElement('h3');
        title.innerHTML = `
            <span class="step-number">${index + 1}</span>
            ${step.title}
        `;
        
        const content = document.createElement('div');
        content.innerHTML = step.content;
        
        stepDiv.appendChild(title);
        stepDiv.appendChild(content);
        container.appendChild(stepDiv);
    });
    
    return container;
}

// Exporter pour utilisation globale
window.codeSandbox = codeSandbox;
window.interactiveDemo = interactiveDemo;
window.processExecutableCode = processExecutableCode;
window.createStepByStepExplanation = createStepByStepExplanation;
