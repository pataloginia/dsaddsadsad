import './App.css'
import { AudioEngineProvider } from './context/AudioEngineContext'
import { Studio } from './components/Studio'

function App() {
  return (
    <AudioEngineProvider>
      <Studio />
    </AudioEngineProvider>
  )
}

export default App
