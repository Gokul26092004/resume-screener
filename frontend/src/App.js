import { useState } from "react";
import axios from "axios";

function App() {
  const [jd, setJd] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const analyzeCandidates = async () => {
    try {
      setLoading(true);

      const response = await axios.post(
        "http://localhost:8000/resume/rank",
        {
          job_description: jd,
          top_k: 10,
          min_score: 0,
        }
      );

      setResults(response.data.results);
    } catch (error) {
      console.error(error);
      alert("API call failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        maxWidth: "1200px",
        margin: "auto",
        padding: "20px",
        fontFamily: "Arial",
      }}
    >
      <h1>🤖 AI Resume Screener</h1>

      <h3>Job Description</h3>

      <textarea
        rows="10"
        style={{
          width: "100%",
          padding: "10px",
          borderRadius: "8px",
        }}
        value={jd}
        onChange={(e) => setJd(e.target.value)}
        placeholder="Paste Job Description Here"
      />

      <br />
      <br />

      <button
        onClick={analyzeCandidates}
        style={{
          padding: "12px 20px",
          backgroundColor: "#2563eb",
          color: "white",
          border: "none",
          borderRadius: "8px",
          cursor: "pointer",
        }}
      >
        Analyze Candidates
      </button>

      <hr style={{ margin: "25px 0" }} />

      <h2>📊 Ranking Results</h2>

      {loading && <p>Analyzing resumes...</p>}

      {results.length > 0 && (
        <table
          style={{
            width: "100%",
            borderCollapse: "collapse",
          }}
        >
          <thead>
            <tr
              style={{
                backgroundColor: "#f3f4f6",
              }}
            >
              <th style={th}>Rank</th>
              <th style={th}>Name</th>
              <th style={th}>Email</th>
              <th style={th}>Score</th>
              <th style={th}>Status</th>
              <th style={th}>Resume</th>
            </tr>
          </thead>

          <tbody>
            {results.map((candidate, index) => (
              <tr key={candidate.resume_id}>
                <td style={td}>{index + 1}</td>

                <td style={td}>{candidate.name}</td>

                <td style={td}>{candidate.email}</td>

                <td style={td}>
                  {(candidate.score * 100).toFixed(2)}%

                  <div
                    style={{
                      width: "120px",
                      border: "1px solid #ccc",
                      marginTop: "5px",
                      borderRadius: "4px",
                    }}
                  >
                    <div
                      style={{
                        width: `${candidate.score * 100}%`,
                        height: "10px",
                        backgroundColor:
                          candidate.score > 0.6
                            ? "green"
                            : candidate.score > 0.3
                            ? "orange"
                            : "red",
                        borderRadius: "4px",
                      }}
                    />
                  </div>
                </td>

                <td style={td}>
                  {candidate.score >= 0.3
                    ? "✅ Shortlisted"
                    : "❌ Rejected"}
                </td>

                <td style={td}>{candidate.filename}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

const th = {
  border: "1px solid #ddd",
  padding: "12px",
  textAlign: "left",
};

const td = {
  border: "1px solid #ddd",
  padding: "12px",
};

export default App;