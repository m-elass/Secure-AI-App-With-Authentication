import ClerkProviderWithRoutes from "./auth/ClerkProviderWithRoutes.jsx"
import {Routes, Route} from "react-router-dom"
import {Layout} from "./layout/Layout.jsx"
import {ChallengeGenerator} from "./challenge/ChallengeGenerator.jsx"
import {HistoryPanel} from "./history/HistoryPanel.jsx"
import {AuthenticationPage} from "./auth/AuthenticationPage.jsx"
import {SubjectProvider} from "./utils/SubjectContext.jsx"
import {useApi} from "./utils/api.js"
import './App.css'

function AppShell() {
    const {makeRequest} = useApi()
    return (
        <SubjectProvider apiClient={makeRequest}>
            <Routes>
                <Route path="/sign-in/*" element={<AuthenticationPage />} />
                <Route path="/sign-up" element={<AuthenticationPage />} />
                <Route element={<Layout />}>
                    <Route path="/" element={<ChallengeGenerator />}/>
                    <Route path="/history" element={<HistoryPanel />}/>
                </Route>
            </Routes>
        </SubjectProvider>
    )
}

function App() {
    return (
        <ClerkProviderWithRoutes>
            <AppShell />
        </ClerkProviderWithRoutes>
    )
}

export default App
