// Generated placeholder — delete when you add real code
use anyhow::Result;
use askama::Template;
use askama_axum::Response;
use axum::{Router, routing::get};
use tower_http::services::ServeDir;

#[derive(Template)]
#[template(path = "index.html")]
struct IndexTemplate {
    message: String,
}

#[derive(Template)]
#[template(path = "message.html")]
struct MessageTemplate {
    message: String,
}

async fn index() -> Response {
    askama_axum::into_response(&IndexTemplate {
        message: "Hello from HTMX!".to_string(),
    })
}

async fn message() -> Response {
    askama_axum::into_response(&MessageTemplate {
        message: "Reloaded via HTMX!".to_string(),
    })
}

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt::init();

    let app = Router::new()
        .route("/", get(index))
        .route("/message", get(message))
        .nest_service("/static", ServeDir::new("static"));

    let listener = tokio::net::TcpListener::bind("0.0.0.0:3000").await?;
    tracing::info!("listening on {}", listener.local_addr()?);
    axum::serve(listener, app).await?;
    Ok(())
}

#[cfg(test)]
mod tests {
    #[test]
    fn placeholder() {}
}
