import "react"
import {useState} from "react"

// Letras A, B, C, D para los círculos a la izquierda de cada opción
const LETTERS = ["A", "B", "C", "D"]

/**
 * Heurística para detectar bloques de código en el enunciado:
 * si una línea contiene tokens propios de Python (def, class, import,
 * self., =, (...), etc.) y va seguida de más líneas en la misma vena,
 * la agrupamos como bloque <pre>.
 *
 * Devuelve un array de nodos React: strings o bloques <pre>.
 */
function renderTitleWithCode(title) {
    if (!title || typeof title !== "string") return title

    const lines = title.split("\n")
    const codeRegex = /^(\s*)(class |def |import |from |if |else|elif |for |while |return |print\(|self\.|[a-zA-Z_]\w*\s*=\s*|@)/
    const inlineCodeRegex = /[{}\[\]()]|->/

    const nodes = []
    let buffer = []
    let codeBuffer = []
    let inCode = false

    const flushText = () => {
        if (buffer.length > 0) {
            nodes.push(
                <span key={`t-${nodes.length}`}>{buffer.join("\n")}{"\n"}</span>
            )
            buffer = []
        }
    }

    const flushCode = () => {
        if (codeBuffer.length > 0) {
            // Quitamos líneas vacías al final del bloque
            while (codeBuffer.length > 0 && codeBuffer[codeBuffer.length - 1].trim() === "") {
                codeBuffer.pop()
            }
            if (codeBuffer.length > 0) {
                nodes.push(
                    <pre key={`c-${nodes.length}`} className="code-block">
                        {codeBuffer.join("\n")}
                    </pre>
                )
            }
            codeBuffer = []
        }
    }

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i]
        const trimmed = line.trim()
        const isCodeLine = codeRegex.test(line) ||
            (trimmed !== "" && line.startsWith("    ")) ||
            (trimmed !== "" && line.startsWith("\t"))

        if (isCodeLine) {
            // Cambio: salgo de modo texto y entro en modo código
            if (!inCode) {
                flushText()
                inCode = true
            }
            codeBuffer.push(line)
        } else {
            // Línea no-código
            if (inCode) {
                // Si es línea vacía DENTRO de un bloque de código, la conservamos
                // siempre que la siguiente línea sea código (espacio interno).
                if (trimmed === "" && i + 1 < lines.length && codeRegex.test(lines[i + 1])) {
                    codeBuffer.push(line)
                    continue
                }
                flushCode()
                inCode = false
            }
            buffer.push(line)
        }
    }

    flushText()
    flushCode()

    return nodes
}

/**
 * Pinta partes del texto entre backticks como <code> y partes con saltos
 * de línea como párrafos. Para títulos sin código de varias líneas.
 */
function renderInlineMarkdown(text) {
    if (!text) return text
    const parts = text.split(/(`[^`]+`)/g)
    return parts.map((p, i) =>
        p.startsWith("`") && p.endsWith("`")
            ? <code key={i}>{p.slice(1, -1)}</code>
            : <span key={i}>{p}</span>
    )
}

export function MCQChallenge({challenge, showExplanation = false}) {
    const [selectedOption, setSelectedOption] = useState(
        showExplanation ? challenge.correct_answer_id : null
    )
    const [revealed, setRevealed] = useState(showExplanation)

    const options = typeof challenge.options === "string"
        ? JSON.parse(challenge.options)
        : challenge.options

    const handleOptionSelect = (index) => {
        if (revealed) return
        setSelectedOption(index)
        setRevealed(true)
    }

    const getOptionClass = (index) => {
        if (!revealed) return "option"
        if (index === challenge.correct_answer_id) return "option correct disabled"
        if (selectedOption === index) return "option incorrect disabled"
        return "option dimmed disabled"
    }

    const difficulty = (challenge.difficulty || "easy").toLowerCase()
    const diffLabel = difficulty === "easy"
        ? "Fácil"
        : difficulty === "medium" ? "Medio" : "Difícil"

    const renderedTitle = renderTitleWithCode(challenge.title)
    const hasCode = renderedTitle && renderedTitle.some(
        n => n && n.props && n.props.className === "code-block"
    )

    return (
        <div className="challenge-display">
            <div className="challenge-meta">
                <span className={`difficulty-badge ${difficulty}`}>
                    <span className="dot" aria-hidden="true"></span>
                    {diffLabel}
                </span>
                {challenge.timestamp && (
                    <span className="challenge-timestamp">
                        {new Date(challenge.timestamp).toLocaleString("es-ES", {
                            day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit"
                        })}
                    </span>
                )}
            </div>

            <div className={`challenge-title ${hasCode ? "has-code" : ""}`}>
                {hasCode ? renderedTitle : renderInlineMarkdown(challenge.title)}
            </div>

            <div className="options" role="radiogroup" aria-label="Opciones de respuesta">
                {options.map((option, index) => (
                    <div
                        className={getOptionClass(index)}
                        key={index}
                        onClick={() => handleOptionSelect(index)}
                        role="radio"
                        aria-checked={selectedOption === index}
                        tabIndex={revealed ? -1 : 0}
                        onKeyDown={(e) => {
                            if (!revealed && (e.key === "Enter" || e.key === " ")) {
                                e.preventDefault()
                                handleOptionSelect(index)
                            }
                        }}
                    >
                        <div className="option-letter">{LETTERS[index]}</div>
                        <div className="option-text">
                            {renderInlineMarkdown(option)}
                        </div>
                    </div>
                ))}
            </div>

            {revealed && challenge.explanation && (
                <div className="explanation">
                    <div className="explanation-header">
                        <div className="explanation-icon" aria-hidden="true">i</div>
                        <h4>Explicación</h4>
                    </div>
                    <p>{renderInlineMarkdown(challenge.explanation)}</p>
                </div>
            )}
        </div>
    )
}
