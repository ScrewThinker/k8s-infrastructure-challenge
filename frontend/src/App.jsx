import { useEffect, useState } from 'react'

export default function App() {
  const [state, setState] = useState({ loading: true })

  useEffect(() => {
    fetch('/api/info')
      .then(async (response) => {
        if (!response.ok) throw new Error(`Backend returned HTTP ${response.status}`)
        return response.json()
      })
      .then((data) => setState({ loading: false, data }))
      .catch((error) => setState({ loading: false, error: error.message }))
  }, [])

  return (
    <main>
      <section className="card">
        <p className="eyebrow">DEVOPS ENGINEER · INFRASTRUCTURE CHALLENGE</p>
        <h1>React → Kubernetes → Python</h1>
        <p className="intro">
          Two independently containerized services, delivered by GitOps and observed with Prometheus.
        </p>

        <div className={`status ${state.error ? 'error' : state.loading ? 'loading' : 'ready'}`}>
          <span className="dot" aria-hidden="true" />
          {state.loading && <span>Connecting to backend…</span>}
          {state.error && <span>Backend unavailable: {state.error}</span>}
          {state.data && <span>{state.data.message}</span>}
        </div>

        {state.data && (
          <dl>
            <div><dt>Backend</dt><dd>{state.data.backend}</dd></div>
            <div><dt>Serving pod</dt><dd>{state.data.pod}</dd></div>
            <div><dt>Delivery</dt><dd>GitHub Actions + Argo CD</dd></div>
          </dl>
        )}
      </section>
    </main>
  )
}
