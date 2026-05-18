import "react"
import {SignIn, SignUp, SignedIn, SignedOut} from "@clerk/clerk-react"
import {useLocation} from "react-router-dom"

export function AuthenticationPage() {
    const location = useLocation()
    const isSignUp = location.pathname.startsWith("/sign-up")

    return (
        <div className="auth-container">
            <div className="auth-brand">
                <div className="auth-brand-logo" aria-hidden="true">P</div>
                <h1>PER Quiz</h1>
                <p>
                    Preguntas tipo test al estilo del examen real de Programación en Entornos de Red.
                    Genera, responde y aprende.
                </p>
            </div>

            <SignedOut>
                {isSignUp
                    ? <SignUp routing="path" path="/sign-up" signInUrl="/sign-in"/>
                    : <SignIn routing="path" path="/sign-in" signUpUrl="/sign-up"/>}
            </SignedOut>

            <SignedIn>
                <div className="redirect-message">
                    Ya has iniciado sesión.
                </div>
            </SignedIn>
        </div>
    )
}
