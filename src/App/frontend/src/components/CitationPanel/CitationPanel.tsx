import React, { useMemo, useState } from 'react';
// import sampledata from '../../sampleResponseCitation.json';
import ReactMarkdown from 'react-markdown';
import { Stack } from '@fluentui/react';
import { DismissRegular } from '@fluentui/react-icons';
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
// import styles from "./Chat.module.css";
// import { AskResponse } from '../../api/models';
import { useAppContext } from '../../state/useAppContext';
import { actionConstants } from '../../state/ActionConstants';
import "./CitationPanel.css";
interface Props {
    activeCitation: any
}

const CitationPanel = ({ activeCitation }: Props) => {
    // console.log("activeCitation", activeCitation);
    const { dispatch } = useAppContext()
    // const [activeCitation, setActiveCitation] =
    //     useState<
    //         [
    //             content: string,
    //             id: string,
    //             title: string,
    //             filepath: string,
    //             url: string,
    //             metadata: string,
    //         ]
    //     >();

    const onCloseCitation = () => {
        dispatch({  type: actionConstants.UPDATE_CITATION,payload: { activeCitation: null, showCitation: false }})
    }
    return (
        <div className='citationPanel'>

            <Stack.Item
                // className={`${styles.citationPanel} ${styles.mobileStyles}`}
            >
                <Stack
                    horizontal
                    // className={styles.citationPanelHeaderContainer}
                    horizontalAlign="space-between"
                    verticalAlign="center"
                >
                    <div
                        role="heading"
                        aria-level={2}
                        style={{
                            fontWeight: "600",
                            fontSize: '16px'
                        }}
                        >

                    {/* // className={styles.citationPanelHeader} */}
                    Citations
                    </div>
                    <DismissRegular
                        role="button"
                        onKeyDown={(e) =>
                            e.key === " " || e.key === "Enter"
                                ? onCloseCitation()
                                : () => { }
                        }
                        tabIndex={0}
                        // className={styles.citationPanelDismiss}
                        onClick={onCloseCitation}
                    />
                </Stack>
                <h5
                    // className={`${styles.citationPanelTitle} ${styles.mobileCitationPanelTitle}`}
                >
                    {activeCitation.title}
                </h5>
                {/* <div className='citationPanelInner'
                    // className={`${styles.citationPanelDisclaimer} ${styles.mobileCitationPanelDisclaimer}`}
                >
                    Tables, images, and other special formatting not shown in this
                    preview. Please follow the link to review the original document.
                </div> */}
                <ReactMarkdown
                // className={`${styles.citationPanelContent} ${styles.mobileCitationPanelContent}`}
                children={activeCitation?.content}
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeRaw]}
              />
            </Stack.Item>
        </div>)
};


export default CitationPanel;