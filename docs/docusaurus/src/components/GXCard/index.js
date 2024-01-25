import React from 'react';
import styles from './styles.module.css';
import cn from 'clsx';
import { useThemeConfig } from '@docusaurus/theme-common';
import useBaseUrl from "@docusaurus/useBaseUrl";

function useGXCardConfig() {
  // TODO temporary casting until ThemeConfig type is improved
  return useThemeConfig().gxCard;
}

export default function gxCard(
  {
    title,
    description
  }
) {
  const content = useGXCardConfig();
  return (
    <div className={styles.gxCard} id="gxCard">
      <div className={styles.gxCard__inner_container}>
        <h1 className={styles.gxCard__title}>{title || content.title}</h1>
        <h4 className={styles.gxCard__description}>{description || content.description}</h4>
        <img className={styles.gxCard__image} src={useBaseUrl('img/expectations_circle.png')} alt=''/>
        <div className={styles.gxCard__buttons}>
            <a className={cn(styles.button)} href={content.buttons.primary.href}>{content.buttons.primary.label}</a>
            <a className={cn(styles.button, styles.button__outline)}
               href={content.buttons.secondary.href}>{content.buttons.secondary.label}</a>
        </div>
      </div>
    </div>
  )
}