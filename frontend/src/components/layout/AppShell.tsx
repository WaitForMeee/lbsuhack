import type { PropsWithChildren } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { BrandMark } from "../brand/BrandMark";
import { useCurrentUser, useLogout } from "../../features/auth/hooks";
import "./AppShell.css";

export function AppShell({ children }: PropsWithChildren) {
  const current = useCurrentUser();
  const logout = useLogout();
  const navigate = useNavigate();
  const user = current.data;
  const accountLink = user?.role === "student" ? "/student" : "/organization";
  const leave = () => logout.mutate(undefined, { onSuccess: () => navigate("/") });
  return <div className="site-frame"><header className="site-header"><div className="page-shell header-inner"><BrandMark /><nav className="desktop-nav" aria-label="Основная навигация"><NavLink to="/events">События</NavLink><NavLink to="/organizations">Организации</NavLink>{user?.organization_id && <NavLink to="/partnerships">Партнёрства</NavLink>}</nav><div className="header-actions">{user ? <><NavLink className="button button-ghost" to={accountLink}>{user.full_name.split(" ")[0]}</NavLink><button className="icon-button" onClick={leave} aria-label="Выйти">↗</button></> : <><NavLink className="text-link" to="/login">Войти</NavLink><NavLink className="button button-primary" to="/register">Создать аккаунт</NavLink></>}</div></div></header><main>{children}</main><nav className="mobile-nav" aria-label="Мобильная навигация"><NavLink to="/">⌂<span>Главная</span></NavLink><NavLink to="/events">⌕<span>События</span></NavLink><NavLink to="/organizations">◎<span>Организации</span></NavLink><NavLink to={user ? accountLink : "/login"}>○<span>Профиль</span></NavLink></nav><footer className="site-footer"><div className="page-shell"><BrandMark /><p>Образовательные возможности и партнёрства — в одном месте.</p></div></footer></div>;
}
