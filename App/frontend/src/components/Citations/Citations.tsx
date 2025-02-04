import React, { useMemo } from 'react';
// import sampledata from '../../sampleResponseCitation.json';
// import { AskResponse, Citation } from '../../api/models';
import { parseAnswer } from './AnswerParser';
import { useAppContext } from '../../state/useAppContext';
import { actionConstants } from '../../state/ActionConstants';
// import { parseAnswer } from "./AnswerParser";
// import styles from "./Citations.css";
import "./Citations.css";
import { AskResponse, Citation } from '../../types/AppTypes';

interface Props {
    answer: AskResponse;
    onSpeak?: any;
    isActive?: boolean;
    index: number;
}

const Citations = ({ answer, index }: Props) => {
    // console.log("answer", answer);
    
    const { state, dispatch } = useAppContext();
    const parsedAnswer = useMemo(() => parseAnswer(answer), [answer]);
    // console.log("parsedAnswer::", parsedAnswer);
    const filePathTruncationLimit = 50;
    const createCitationFilepath = (
        citation: Citation,
        index: number,
        truncate: boolean = false
    ) => {
        let citationFilename = "";

        // if (citation.filepath && citation.chunk_id != null) {
        //     if (truncate && citation.filepath.length > filePathTruncationLimit) {
        //         const citationLength = citation.filepath.length;
        //         citationFilename = `${citation.filepath.substring(0, 20)}...${citation.filepath.substring(citationLength - 20)} - Part ${citation.chunk_id}`;
        //     } else {
        //         citationFilename = `${citation.filepath} - Part ${citation.chunk_id}`;
        //     }
        // } else {
            citationFilename = `Citation ${index}`;
        // }
        return citationFilename;
    };

    const onCitationClicked = (
        citation: Citation
    ) => {
        dispatch({
            type: actionConstants.UPDATE_CITATION,
            payload: { showCitation: true, activeCitation: citation },
        });
    };


    return (
        <div
            style={{
                marginTop: 8,
                display: "flex",
                flexDirection: "column",
                height: "100%",
                gap: "4px",
                maxWidth: "100%",
            }}
        >
            {parsedAnswer.citations.map((citation, idx) => {
                return (
                    <span
                        role="button"
                        onKeyDown={(e) =>
                            e.key === " " || e.key === "Enter"
                                ? onCitationClicked(citation)
                                : () => { }
                        }
                        tabIndex={0}
                        title={createCitationFilepath(citation, ++idx)}
                        key={idx}
                        onClick={() => onCitationClicked(citation)}
                     className={"citationContainer"}
                    >
                        <div
                             className={"citation"} 
                            key={idx}>
                            {idx}
                        </div>
                        {createCitationFilepath(citation, idx, true)}
                    </span>
                );
            })}
        </div>)
};


export default Citations;