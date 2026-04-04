use axum::{
    async_trait,
    extract::{FromRequestParts, FromRef},
    http::{request::Parts, StatusCode},
    response::{IntoResponse, Response},
};
use std::sync::Arc;
use crate::state::AppState;

pub struct AuthContext {
    pub token_or_key: String,
    pub is_virtual_key: bool,
}

#[async_trait]
impl<S> FromRequestParts<S> for AuthContext
where
    Arc<AppState>: FromRef<S>,
    S: Send + Sync,
{
    type Rejection = Response;

    async fn from_request_parts(parts: &mut Parts, state: &S) -> Result<Self, Self::Rejection> {
        let app_state = Arc::<AppState>::from_ref(state);

        let header_token = match crate::handlers::extract_token(&parts.headers) {
            Some(t) if t.len() >= 10 => t,
            _ => return Err((StatusCode::UNAUTHORIZED, "Missing Token").into_response()),
        };

        // 仅仅验证虚拟 Key 是否合法，不负责路由真实账号 (因为此处不知道用户请求的模型是什么，无法根据配额挑号)
        let is_virtual_key = app_state.key_manager.is_valid(&header_token).await;
        
        // 如果它既不是我们派发的虚拟 Key，也没有直连的格式特征，安全起见在此拦截
        // 注意：放行 "sk-" 前缀的密钥以兼容 new-api / one-api 等第三方网关转发场景
        if !is_virtual_key
            && !header_token.starts_with("1//")
            && !header_token.starts_with("ya29.")
            && !header_token.starts_with("sk-")
        {
            return Err((StatusCode::UNAUTHORIZED, "Invalid authentication key format.").into_response());
        }

        Ok(AuthContext {
            token_or_key: header_token,
            is_virtual_key,
        })
    }
}
