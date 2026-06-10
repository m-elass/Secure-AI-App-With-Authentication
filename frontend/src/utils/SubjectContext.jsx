import "react"
import {createContext, useContext, useEffect, useState, useCallback, useMemo} from "react"

/**
 * SubjectContext — guarda la asignatura activa y, opcionalmente, el área
 * activa dentro de esa asignatura.
 *
 * Persistencia (localStorage):
 *   - perquiz.activeSubject:  id de la asignatura
 *   - perquiz.activeArea.<subject>:  id de área (uno por asignatura)
 *
 * Convenciones:
 *   - activeArea === null  → "todas las áreas" (repaso global)
 *   - activeArea === "metabolismo"  → solo metabolismo
 *   - activeArea === "genetica"  → solo genética
 *
 * Las asignaturas sin áreas (PER) ignoran este concepto.
 */

const SUBJECT_KEY = "perquiz.activeSubject"
const AREA_KEY_PREFIX = "perquiz.activeArea."
const DEFAULT_SUBJECT = "per"

const SEED_SUBJECTS = [
    {
        id: "per",
        name: "PER",
        full_name: "Programación en Entornos de Red",
        description: "Python OOP, HTTP, sockets, JSON",
        accent: "violet",
        areas: [],
    },
    {
        id: "biochem",
        name: "Bioquímica",
        full_name: "Bioquímica y Biología Molecular",
        description: "Metabolismo y genética molecular",
        accent: "emerald",
        areas: [
            {id: "metabolismo", name: "Metabolismo",
             description: "Glucólisis, Krebs, β-oxidación, ureogénesis, hormonas"},
            {id: "genetica",    name: "Genética",
             description: "Replicación, transcripción, traducción, ingeniería"},
        ],
    },
]

const SubjectContext = createContext(null)

function readStoredArea(subjectId) {
    try {
        const v = localStorage.getItem(AREA_KEY_PREFIX + subjectId)
        // null = "todas"; ""  también lo interpretamos como null
        return v && v !== "" ? v : null
    } catch {
        return null
    }
}

function writeStoredArea(subjectId, area) {
    try {
        if (area === null || area === "") {
            localStorage.removeItem(AREA_KEY_PREFIX + subjectId)
        } else {
            localStorage.setItem(AREA_KEY_PREFIX + subjectId, area)
        }
    } catch { /* ignore */ }
}

export function SubjectProvider({children, apiClient}) {
    const [subjects, setSubjects] = useState(SEED_SUBJECTS)
    const [activeSubject, setActiveSubjectState] = useState(() => {
        try {
            return localStorage.getItem(SUBJECT_KEY) || DEFAULT_SUBJECT
        } catch {
            return DEFAULT_SUBJECT
        }
    })
    // Áreas activas por asignatura (sólo aplica a las que tienen subáreas)
    const [areaBySubject, setAreaBySubject] = useState(() => {
        const out = {}
        for (const s of SEED_SUBJECTS) {
            if (s.areas?.length) out[s.id] = readStoredArea(s.id)
        }
        return out
    })

    // Carga del catálogo desde el backend
    useEffect(() => {
        if (!apiClient) return
        apiClient("subjects")
            .then((data) => {
                if (data?.subjects?.length) {
                    setSubjects(data.subjects)
                    // Si la asignatura guardada ya no existe, caemos a la primera
                    if (!data.subjects.find(s => s.id === activeSubject)) {
                        setActiveSubjectState(data.subjects[0].id)
                    }
                    // Inicializa áreas si vinieron asignaturas nuevas
                    setAreaBySubject((prev) => {
                        const next = {...prev}
                        for (const s of data.subjects) {
                            if (s.areas?.length && !(s.id in next)) {
                                next[s.id] = readStoredArea(s.id)
                            }
                        }
                        return next
                    })
                }
            })
            .catch((err) => console.warn("No se pudieron cargar las asignaturas:", err))
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [apiClient])

    // Sincroniza body[data-subject], body[data-accent] y localStorage del subject
    useEffect(() => {
        try { localStorage.setItem(SUBJECT_KEY, activeSubject) } catch { /* ignore */ }
        const meta = subjects.find(s => s.id === activeSubject)
        if (meta) {
            document.body.dataset.subject = activeSubject
            document.body.dataset.accent = meta.accent
        }
    }, [activeSubject, subjects])

    const setActiveSubject = useCallback((id) => {
        if (subjects.find(s => s.id === id)) {
            setActiveSubjectState(id)
        }
    }, [subjects])

    // Área activa: depende de la asignatura activa
    const activeArea = areaBySubject[activeSubject] ?? null

    const setActiveArea = useCallback((area) => {
        // Normalizamos: "" o undefined → null ("todas")
        const normalized = (area === "" || area === undefined) ? null : area
        setAreaBySubject((prev) => ({...prev, [activeSubject]: normalized}))
        writeStoredArea(activeSubject, normalized)
    }, [activeSubject])

    const activeMeta = useMemo(
        () => subjects.find(s => s.id === activeSubject) || subjects[0],
        [subjects, activeSubject]
    )

    const activeAreaMeta = useMemo(() => {
        if (!activeArea) return null
        return activeMeta?.areas?.find(a => a.id === activeArea) || null
    }, [activeMeta, activeArea])

    const value = {
        subjects,
        activeSubject,
        activeMeta,
        setActiveSubject,
        activeArea,            // null | "metabolismo" | "genetica" | ...
        activeAreaMeta,        // metadata del área activa, o null
        setActiveArea,
        hasAreas: !!activeMeta?.areas?.length,
    }

    return (
        <SubjectContext.Provider value={value}>
            {children}
        </SubjectContext.Provider>
    )
}

export function useSubject() {
    const ctx = useContext(SubjectContext)
    if (!ctx) {
        throw new Error("useSubject debe usarse dentro de un SubjectProvider")
    }
    return ctx
}