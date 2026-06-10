import "react"
import {useState, useEffect} from "react"
import {MCQChallenge} from "./MCQChallenge.jsx"
import {useApi} from "../utils/api.js"
import {useSubject} from "../utils/SubjectContext.jsx"

const DIFFICULTIES = [
    {id: "easy",   name: "Fácil",   className: "easy"},
    {id: "medium", name: "Medio",   className: "medium"},
    {id: "hard",   name: "Difícil", className: "hard"},
]

// Descripciones contextualizadas — ahora también por área de bioquímica
const DIFFICULTY_DESCRIPTIONS = {
    per: {
        easy:   "Conceptos básicos: clases, verbos HTTP, JSON",
        medium: "Herencia, REST, sockets, loads vs load",
        hard:   "Análisis de código, traza HTTP, override avanzado",
    },
    "biochem:genetica": {
        easy:   "Conceptos clave: enzimas, código genético, replicación",
        medium: "Mecanismos: transcripción, traducción, operones",
        hard:   "Regulación eucariota, ingeniería genética, CRISPR",
    },
    "biochem:metabolismo": {
        easy:   "Termodinámica, hormonas, glucólisis, ciclo de Krebs",
        medium: "Gluconeogénesis, β-oxidación, cadena respiratoria, ureogénesis",
        hard:   "Regulación alostérica y hormonal, integración del metabolismo",
    },
    "biochem:all": {
        easy:   "Conceptos básicos mezclados de toda la bioquímica",
        medium: "Mecanismos clave de metabolismo y genética",
        hard:   "Integración avanzada de toda la asignatura",
    },
}

const LOADING_MESSAGES = {
    per: [
        "Consultando el temario de PER...",
        "Diseñando distractores plausibles...",
        "Buscando ese bug sutil en el código...",
        "Revisando los apuntes de la URJC...",
    ],
    biochem: [
        "Consultando el temario de bioquímica...",
        "Diseñando distractores plausibles...",
        "Buscando ese matiz que separa los conceptos...",
        "Revisando los apuntes de la profesora...",
    ],
}

const FALLBACK_LOADING = ["Generando pregunta..."]

function descKey(subject, area) {
    if (subject !== "biochem") return subject
    return area ? `biochem:${area}` : "biochem:all"
}

export function ChallengeGenerator() {
    const [challenge, setChallenge] = useState(null)
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState(null)
    const [difficulty, setDifficulty] = useState("easy")
    const [loadingMsg, setLoadingMsg] = useState("")
    const {makeRequest} = useApi()
    const {
        activeSubject, activeMeta,
        activeArea, activeAreaMeta, setActiveArea, hasAreas,
    } = useSubject()

    // Limpia challenge al cambiar de asignatura o área
    useEffect(() => {
        setChallenge(null)
        setError(null)
    }, [activeSubject, activeArea])

    // Rotación de mensajes de carga
    useEffect(() => {
        if (!isLoading) return
        const pool = LOADING_MESSAGES[activeSubject] || FALLBACK_LOADING
        let i = Math.floor(Math.random() * pool.length)
        setLoadingMsg(pool[i])
        const id = setInterval(() => {
            i = (i + 1) % pool.length
            setLoadingMsg(pool[i])
        }, 1800)
        return () => clearInterval(id)
    }, [isLoading, activeSubject])

    const generateChallenge = async () => {
        setIsLoading(true)
        setError(null)
        try {
            const body = {
                difficulty,
                subject: activeSubject,
            }
            // Solo enviamos area si la asignatura tiene áreas y el usuario eligió una
            if (hasAreas && activeArea) {
                body.area = activeArea
            }
            const data = await makeRequest("generate-challenge", {
                method: "POST",
                body: JSON.stringify(body),
            })
            setChallenge(data)
        } catch (err) {
            setError(err.message || "No se pudo generar la pregunta.")
        } finally {
            setIsLoading(false)
        }
    }

    const descriptions =
        DIFFICULTY_DESCRIPTIONS[descKey(activeSubject, activeArea)] ||
        DIFFICULTY_DESCRIPTIONS.per

    // Texto del subtítulo
    let subtitleScope = activeMeta?.full_name || activeMeta?.name || activeSubject
    if (hasAreas && activeAreaMeta) {
        subtitleScope = `${activeMeta.name} · ${activeAreaMeta.name}`
    } else if (hasAreas && !activeArea) {
        subtitleScope = `${activeMeta.name} · todas las áreas`
    }

    return (
        <div className="challenge-container">
            <h2 className="section-title">Generador de preguntas</h2>
            <p className="section-subtitle">
                Preguntas tipo test al estilo del examen real de{" "}
                <strong>{subtitleScope}</strong>. Elige una dificultad y empieza a practicar.
            </p>

            {/* Sub-selector de área (solo si la asignatura tiene áreas) */}
            {hasAreas && (
                <div className="area-selector">
                    <label className="difficulty-label">Área</label>
                    <div className="area-tabs" role="radiogroup" aria-label="Área dentro de la asignatura">
                        <button
                            type="button"
                            role="radio"
                            aria-checked={activeArea === null}
                            className={`area-tab ${activeArea === null ? "active" : ""}`}
                            onClick={() => setActiveArea(null)}
                            disabled={isLoading}
                        >
                            <span className="area-tab-name">Todo</span>
                            <span className="area-tab-desc">Mezcla aleatoria de las dos áreas</span>
                        </button>
                        {activeMeta.areas.map((a) => (
                            <button
                                key={a.id}
                                type="button"
                                role="radio"
                                aria-checked={activeArea === a.id}
                                className={`area-tab ${activeArea === a.id ? "active" : ""}`}
                                onClick={() => setActiveArea(a.id)}
                                disabled={isLoading}
                            >
                                <span className="area-tab-name">{a.name}</span>
                                <span className="area-tab-desc">{a.description}</span>
                            </button>
                        ))}
                    </div>
                </div>
            )}

            <div className="difficulty-selector">
                <label className="difficulty-label">Dificultad</label>
                <div className="difficulty-pills" role="radiogroup" aria-label="Seleccionar dificultad">
                    {DIFFICULTIES.map((d) => (
                        <button
                            key={d.id}
                            type="button"
                            role="radio"
                            aria-checked={difficulty === d.id}
                            className={`diff-pill ${d.className} ${difficulty === d.id ? "selected" : ""}`}
                            onClick={() => setDifficulty(d.id)}
                            disabled={isLoading}
                        >
                            <span className="diff-pill-name">
                                <span className="diff-pill-dot" aria-hidden="true"></span>
                                {d.name}
                            </span>
                            <span className="diff-pill-desc">{descriptions[d.id]}</span>
                        </button>
                    ))}
                </div>
            </div>

            <button
                onClick={generateChallenge}
                disabled={isLoading}
                className="generate-button"
            >
                {isLoading ? (
                    <>
                        <span className="spinner" aria-hidden="true"></span>
                        <span>{loadingMsg}</span>
                    </>
                ) : (
                    <>
                        <span>Generar pregunta</span>
                        <span aria-hidden="true">→</span>
                    </>
                )}
            </button>

            {error && (
                <div className="error-message" role="alert">
                    <span aria-hidden="true">⚠</span>
                    <span>{error}</span>
                </div>
            )}

            {challenge && !isLoading && (
                <MCQChallenge key={challenge.id} challenge={challenge}/>
            )}
        </div>
    )
}