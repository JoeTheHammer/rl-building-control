import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { ROUTES } from './lib/routes.tsx'
import NavigationBar from './components/general/navigation-bar.tsx'

function App() {
  return (
    <>
      <BrowserRouter>
        <NavigationBar />
        <Routes>
          {ROUTES.map((route) => (
            <Route
              key={route.path}
              path={route.path}
              element={route.component}
            />
          ))}
        </Routes>
      </BrowserRouter>
    </>
  )
}

export default App
