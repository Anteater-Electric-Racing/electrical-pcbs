// Lets TypeScript import image files; Vite turns them into asset URLs.
declare module "*.png" {
  const url: string;
  export default url;
}
